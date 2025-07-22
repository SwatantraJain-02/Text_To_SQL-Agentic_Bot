import streamlit as st
import time
from datetime import datetime

def initialize_session_state():
    """Initialize Streamlit session state for thread management."""
    if 'threads' not in st.session_state:
        st.session_state.threads = {}
    
    if 'current_thread_id' not in st.session_state:
        # Use timestamp-based ID generation instead of asyncio
        thread_id = int(time.time() * 1000)  # Millisecond timestamp for uniqueness
        
        st.session_state.threads[thread_id] = {
            'workflow': None,
            'graph': None,
            'messages': [],
            'created_at': datetime.now(),
            'title': 'New Conversation'
        }
        st.session_state.current_thread_id = thread_id
    
    if 'thread_counter' not in st.session_state:
        st.session_state.thread_counter = 1

def restart_application():
    """Clear all session state and restart the app."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
