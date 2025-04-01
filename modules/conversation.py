import os
from typing import Any, Dict, List

import streamlit as st
from auto_gptq import AutoGPTQForCausalLM
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.llms import LlamaCpp
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from modules.templates import bot_template, user_template
import torch

class ChatState(BaseModel):
    input: str
    chat_history: List[Any] = []
    retrieved_docs: List[Dict[str, Any]] = []
    response: str = None


def get_llm():
    """Initialize the appropriate LLM based on user selection."""
    if st.session_state.get("model_type_selector") == "OpenAI GPT-3.5":
        return ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
    else:
        if "local_model_path" not in st.session_state:
            raise ValueError("Please upload a local model first")
        
        model_path = st.session_state.local_model_path
        file_ext = os.path.splitext(model_path)[1].lower()
        
        if file_ext == ".gguf":
            return LlamaCpp(
                model_path=model_path,
                max_tokens=st.session_state.get("max_local_tokens_input", 512),
                n_gpu_layers=st.session_state.get("gpu_layers_input", 0),
                temperature=st.session_state.get("temperature_input", 0.1),
                top_p=st.session_state.get("top_p_input", 0.95),
                repeat_penalty=st.session_state.get("repeat_penalty_input", 1.2),
                n_ctx=st.session_state.get("n_ctx_input", 4096),
                verbose=False
            )
        elif file_ext == ".safetensors":
            # Load GPTQ model
            model_basename = os.path.basename(model_path).replace(".safetensors", "")
            model = AutoGPTQForCausalLM.from_quantized(
                model_dir=os.path.dirname(model_path),
                model_basename=model_basename,
                use_safetensors=True,
                trust_remote_code=True,
                device="cuda:0" if torch.cuda.is_available() else "cpu",
                use_triton=False,
                quantize_config=None
            )
            tokenizer = AutoTokenizer.from_pretrained(
                os.path.dirname(model_path)
            )
            return pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=st.session_state.get("max_local_tokens_input", 512)
            )
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")


def handle_userinput(user_question: str) -> None:
    """Handle user input and update the conversation."""
    # Create a container for chat messages
    chat_container = st.container()
    
    # Process the question
    initial_state = ChatState(
        input=user_question,
        chat_history=st.session_state.message_history.messages
    )
    
    if st.session_state.conversation:
        result = st.session_state.conversation.invoke(initial_state)
        
        # Display full history in the container
        with chat_container:
            for message in st.session_state.message_history.messages:
                if isinstance(message, HumanMessage):
                    st.write(user_template.replace("{{MSG}}", message.content), 
                           unsafe_allow_html=True)
                else:
                    st.write(bot_template.replace("{{MSG}}", message.content), 
                           unsafe_allow_html=True)


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
        llm = get_llm()  # Use the selected LLM
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
