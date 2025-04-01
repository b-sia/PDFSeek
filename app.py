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
    
    # Model type selection
    model_type = st.selectbox(
        "Choose Model Type",
        ["OpenAI GPT-3.5", "Local LLM"],
        key="model_type_selector"
    )
    
    # Local model configuration
    if model_type == "Local LLM":
        uploaded_model = st.file_uploader(
            "Upload GGUF Model File",
            type=["gguf"],
            key="model_uploader"
        )
        
        if uploaded_model is not None:
            # Save uploaded model to temporary directory
            model_dir = "./models"
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, uploaded_model.name)
            
            with open(model_path, "wb") as f:
                f.write(uploaded_model.getbuffer())
            
            st.session_state.local_model_path = model_path
            st.success(f"Model saved to: {model_path}")
        
        if "local_model_path" in st.session_state:
            st.code(f"Using model: {st.session_state.local_model_path}")
        
        st.session_state.max_local_tokens = st.number_input(
            "Max Tokens", 100, 4096, 512,
            key="max_local_tokens_input"
        )
        st.session_state.temperature = st.number_input(
            "Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.01, key="temperature_input"
        )
        st.session_state.top_p = st.number_input(
            "Top P", min_value=0.0, max_value=1.0, value=0.95, step=0.01, key="top_p_input"
        )
        st.session_state.repeat_penalty = st.number_input(
            "Repeat Penalty", min_value=0.0, max_value=2.0, value=1.2, step=0.1, key="repeat_penalty_input"
        )
        st.session_state.n_ctx = st.number_input(
            "Context Length (n_ctx)", min_value=1, max_value=4096, value=4096, step=1, key="n_ctx_input"
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