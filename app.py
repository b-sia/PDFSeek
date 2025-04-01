import os
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from PyPDF2 import PdfReader

from htmlTemplates import bot_template, css, user_template


# 1. Define proper State model
class ChatState(BaseModel):
    input: str
    chat_history: List[BaseMessage] = []
    retrieved_docs: List[Dict[str, Any]] = []
    response: str = None


def get_pdf_text(pdf_docs: List[str]) -> str:
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text: str) -> List[str]:
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.split_text(text)


def get_vectorstore(text_chunks: List[str]) -> FAISS:
    embeddings = OpenAIEmbeddings()
    return FAISS.from_texts(text_chunks, embeddings)


# 4. Update the handle_userinput function
def handle_userinput(user_question: str) -> None:
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


def build_conversation_graph(vectorstore: FAISS) -> StateGraph:
    # Initialize message history
    message_history = ChatMessageHistory()
    
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
        
        # Convert documents to strings for context
        context = [doc.page_content for doc in state.retrieved_docs]

        # Create the QA chain with memory
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

    # Build the graph
    workflow = StateGraph(ChatState)
    
    workflow.add_node("handle_input", handle_input)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate_response", generate_response)
    
    workflow.set_entry_point("handle_input")
    workflow.add_edge("handle_input", "retrieve")
    workflow.add_edge("retrieve", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()

def main():
    load_dotenv()
    os.environ["OpenAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "message_history" not in st.session_state:
        st.session_state.message_history = ChatMessageHistory()

    st.header("Chat with multiple PDFs :books:")
    user_question = st.text_input("Ask a question about your documents:")

    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        
        if st.button("Process"):
            with st.spinner("Processing"):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                vectorstore = get_vectorstore(text_chunks)
                st.session_state.conversation = build_conversation_graph(vectorstore)

if __name__ == '__main__':
    main()