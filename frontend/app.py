import streamlit as st
from components.sidebar import render_sidebar
from components.chat_interface import render_chat
from utils.session_state import initialize_session_state

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="AI Agent Supervisor Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
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
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Render components (both are now synchronous)
    render_sidebar()
    render_chat()

if __name__ == "__main__":
    main()
