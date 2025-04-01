from typing import List

import streamlit as st
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from PyPDF2 import PdfReader

from modules.conversation import build_conversation_graph


def get_pdf_text(pdf_docs: List[str]) -> str:
    """Extract text from uploaded PDF documents."""
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text: str) -> List[str]:
    """Split text into manageable chunks."""
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.split_text(text)


def get_vectorstore(text_chunks: List[str]) -> FAISS:
    """Create a vectorstore from text chunks."""
    if st.session_state.get("model_type_selector") == "Local LLM":
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    else:
        embeddings = OpenAIEmbeddings()
    return FAISS.from_texts(text_chunks, embeddings)


def process_uploaded_pdfs(pdf_docs):
    """Process uploaded PDF documents."""
    with st.spinner("Processing"):
        # Clear existing conversation but keep history
        if "conversation" in st.session_state:
            del st.session_state.conversation
            
        raw_text = get_pdf_text(pdf_docs)
        text_chunks = get_text_chunks(raw_text)
        vectorstore = get_vectorstore(text_chunks)
        st.session_state.conversation = build_conversation_graph(vectorstore)
