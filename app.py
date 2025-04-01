import os
import streamlit as st
from dotenv import load_dotenv
from modules.state_management import initialize_session_state
from modules.pdf_processing import process_uploaded_pdfs
from modules.conversation import handle_userinput
from modules.templates import css

def render_sidebar():
    """Render the sidebar for uploading and processing PDFs."""
    st.subheader("Documents")
    pdf_docs = st.file_uploader(
        "Upload your PDFs here and click on 'Process'", accept_multiple_files=True
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