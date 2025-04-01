from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from modules.templates import bot_template, user_template
import streamlit as st
from pydantic import BaseModel
from typing import Any, Dict, List

class ChatState(BaseModel):
    input: str
    chat_history: List[Any] = []
    retrieved_docs: List[Dict[str, Any]] = []
    response: str = None


def handle_userinput(user_question: str) -> None:
    """Handle user input and update the conversation."""
    if "message_history" not in st.session_state:
        st.session_state.message_history = ChatMessageHistory()
    
    initial_state = ChatState(
        input=user_question,
        chat_history=st.session_state.message_history.messages
    )
    
    # Execute the conversation graph
    result = st.session_state.conversation.invoke(initial_state)
    
    # Update displayed messages
    for message in st.session_state.message_history.messages[-2:]:
        if isinstance(message, HumanMessage):
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)


def build_conversation_graph(vectorstore) -> StateGraph:
    """Build the conversation graph."""
    def handle_input(state: ChatState):
        st.session_state.message_history.add_user_message(state.input)
        return ChatState(
            input=state.input,
            chat_history=st.session_state.message_history.messages
        )

    def retrieve(state: ChatState):
        retriever = vectorstore.as_retriever()
        docs = retriever.invoke(state.input)
        return {"retrieved_docs": docs}

    def generate_response(state: ChatState):
        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
        context = [doc.page_content for doc in state.retrieved_docs]
        qa_chain = create_retrieval_chain(
            retriever=vectorstore.as_retriever(),
            combine_docs_chain=create_stuff_documents_chain(
                llm,
                ChatPromptTemplate.from_template(
                    "Answer based on context:\n{context}\n\nChat history:\n{chat_history}\n\nQuestion: {input}"
                )
            )
        )
        response = qa_chain.invoke({
            "input": state.input,
            "chat_history": state.chat_history,
            "context": context
        })
        st.session_state.message_history.add_ai_message(response["answer"])
        return {"response": response["answer"], "chat_history": st.session_state.message_history.messages}

    workflow = StateGraph(ChatState)
    workflow.add_node("handle_input", handle_input)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate_response", generate_response)
    workflow.set_entry_point("handle_input")
    workflow.add_edge("handle_input", "retrieve")
    workflow.add_edge("retrieve", "generate_response")
    workflow.add_edge("generate_response", END)
    return workflow.compile()