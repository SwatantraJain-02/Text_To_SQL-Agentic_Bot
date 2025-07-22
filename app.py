import streamlit as st
from frontend.components.sidebar import render_sidebar
from frontend.components.chat_interface import render_chat
from frontend.utils.session_state import initialize_session_state
import sys
import os

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.append(src_path)


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="AI Agent Supervisor Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown(
        """
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Initialize session state
    initialize_session_state()

    # Render components (both are now synchronous)
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
