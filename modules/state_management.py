import streamlit as st
from langchain_community.chat_message_histories import ChatMessageHistory


def initialize_session_state():
    """Initialize session state variables."""
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "message_history" not in st.session_state:
        st.session_state.message_history = ChatMessageHistory()
    if "chat_displayed" not in st.session_state:
        st.session_state.chat_displayed = False