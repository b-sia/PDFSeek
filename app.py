import os
import streamlit as st
from dotenv import load_dotenv
from modules.state_management import initialize_session_state
from modules.pdf_processing import process_uploaded_pdfs
from modules.conversation import handle_userinput
from modules.templates import css


def render_sidebar():
    """Render the sidebar for model selection and PDF processing."""
    st.subheader("Model Configuration")
    model_type = st.selectbox(
        "Choose Model Type",
        ["OpenAI GPT-3.5", "Local LLM"],
        key="model_type"
    )
    
    if model_type == "Local LLM":
        st.session_state.local_model_path = st.text_input(
            "Local Model Path (e.g., ./models/llama-2-7b.Q4_K_M.gguf)",
            key="local_model_path"
        )
        st.session_state.max_local_tokens = st.number_input(
            "Max Tokens", 100, 4096, 512, key="max_local_tokens"
        )
    
    st.subheader("Document Processing")
    pdf_docs = st.file_uploader(
        "Upload PDFs and click 'Process'", 
        accept_multiple_files=True
    )
    if st.button("Process"):
        process_uploaded_pdfs(pdf_docs)


def main():
    load_dotenv()
    os.environ["OpenAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    initialize_session_state()

    st.header("Chat with multiple PDFs :books:")
    user_question = st.text_input("Ask a question about your documents:")

    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        render_sidebar()


if __name__ == '__main__':
    main()