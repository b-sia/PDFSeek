import os
from typing import List

import streamlit as st
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import \
    create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.llms import HuggingFaceHub
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from PyPDF2 import PdfReader

from htmlTemplates import bot_template, css, user_template


def get_pdf_text(pdf_docs: List[str]) -> str:
    """
    Extracts and returns the text from input PDF.
    Args:
        pdf_docs: List of PDF file objects.
    Returns:
        str: Extracted text from the PDFs.
    """
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()

    return text


def get_text_chunks(text: str) -> List[str]:
    """
    Splits the input text into smaller chunks for processing.

    Args:
        text: The input text to be split into chunks.

    Returns:
        List[str]: A list of text chunks.
    """
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=2000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


def get_vectorstore(text_chunks: List[str]) -> FAISS:
    """
    Creates a vector store from the input text chunks.

    Args:
        text_chunks: A list of text chunks to be stored in the vector store.

    Returns:
        FAISS: The vector store containing the text chunks.
    """
    embeddings = OpenAIEmbeddings()
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(text_chunks, embeddings)
    return vectorstore


def handle_userinput(user_question: str) -> None:
    """
    Handles the user's input question and updates the chat interface.

    Args:
        user_question: The question provided by the user.

    Returns:
        None
    """
    response = st.session_state.conversation({"question": user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)

        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


def get_conversation_chain(vectorstore: FAISS) -> Runnable:
    """
    Creates a conversational retrieval chain using the provided vector store.

    Args:
        vectorstore: The vector store to be used for retrieval.

    Returns:
        ConversationalRetrievalChain: The conversational retrieval chain.
    """
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo"
    )
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Create a prompt template that includes chat history
    retriever_prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder("chat_history"),  # Explicitly reference chat history
        ("user", "Given the conversation history above, rephrase the latest input to be a standalone query:"),
        ("user", "{input}")
    ])

    # Create a prompt for the final response generation
    response_prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question based on the context and chat history:\n\nContext: {context}"),
        MessagesPlaceholder("chat_history"),  # Include chat history again
        ("user", "{input}")
    ])

    # Chain to process retrieved documents + generate final response
    document_chain = create_stuff_documents_chain(llm, response_prompt)

    # Create a history-aware retriever
    history_aware_retriever = create_history_aware_retriever(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        prompt=retriever_prompt
    )

    # Create a retrieval chain
    retrieval_chain = create_retrieval_chain(
        retriever=history_aware_retriever,
        combine_docs_chain=document_chain
    )

    final_chain = retrieval_chain | {
        "chat_history": lambda _: memory.load_memory_variables({})["chat_history"],
        "input": lambda x: x["input"]
    } | memory.save_context

    return final_chain


def main():
    load_dotenv()
    os.environ["OpenAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    st.set_page_config(page_title="Chat with multiple PDFs",
                       page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

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
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)

                # get the text chunks
                text_chunks = get_text_chunks(raw_text)

                # create vector store
                vectorstore = get_vectorstore(text_chunks)

                # create conversation chain
                # takes the history of the conversation and returns the next element of the conversation
                st.session_state.conversation = get_conversation_chain(
                    vectorstore)


if __name__ == '__main__':
    main()