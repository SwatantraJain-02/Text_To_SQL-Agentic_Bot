import streamlit as st
import asyncio
import time
from langchain_core.messages import HumanMessage, AIMessage
from frontend.utils.session_state import restart_application

def render_sidebar():
    """Render the sidebar with thread management controls."""
    with st.sidebar:
        st.header("🧵 Conversation Threads")
        
        # Control buttons - make them synchronous
        if st.button("➕ New Thread", use_container_width=True):
            create_new_thread_sync()
        
        if st.button("🔄 Restart Application", use_container_width=True):
            restart_application()
        
        if st.button("🗑️ Clear Current Thread", use_container_width=True):
            if clear_thread_memory_sync(st.session_state.current_thread_id):
                st.success("Thread memory cleared!")
                st.rerun()
        
        st.divider()
        
        # Thread list
        _render_thread_list()

def create_new_thread_sync():
    """Create a new conversation thread synchronously."""
    thread_id = int(time.time() * 1000)
    st.session_state.thread_counter += 1
    
    st.session_state.threads[thread_id] = {
        'workflow': None,
        'graph': None,
        'messages': [],
        'created_at': time.time(),
        'title': f'Conversation {st.session_state.thread_counter}'
    }
    st.session_state.current_thread_id = thread_id
    st.rerun()

def delete_thread_sync(thread_id: int):
    """Delete a specific thread synchronously."""
    if len(st.session_state.threads) > 1:
        # Clear memory if workflow exists
        thread = st.session_state.threads[thread_id]
        if thread['workflow']:
            try:
                # Store the workflow for cleanup - we'll handle this later
                st.session_state[f'cleanup_thread_{thread_id}'] = True
            except Exception as e:
                st.error(f"Error marking for cleanup: {str(e)}")
        
        del st.session_state.threads[thread_id]
        st.session_state.current_thread_id = list(st.session_state.threads.keys())[0]
        st.rerun()

def clear_thread_memory_sync(thread_id: int):
    """Clear memory for a specific thread synchronously."""
    thread = st.session_state.threads[thread_id]
    if thread['workflow']:
        try:
            # Mark for cleanup and clear UI messages immediately
            st.session_state[f'cleanup_thread_{thread_id}'] = True
            thread['messages'] = []
            return True
        except Exception as e:
            st.error(f"Error clearing memory: {str(e)}")
            return False
    else:
        # Just clear UI messages if no workflow
        thread['messages'] = []
        return True

def _render_thread_list():
    """Render the list of available threads."""
    for thread_id, thread_data in st.session_state.threads.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            is_current = thread_id == st.session_state.current_thread_id
            title = thread_data['title'][:20] + "..." if len(thread_data['title']) > 20 else thread_data['title']
            
            if st.button(
                title,
                key=f"thread_{thread_id}",
                use_container_width=True,
                type="primary" if is_current else "secondary"
            ):
                st.session_state.current_thread_id = thread_id
                st.rerun()
        
        with col2:
            if st.button("📚", key=f"history_{thread_id}", help="Show History"):
                _show_thread_history_sync(thread_id, thread_data)
        
        with col3:
            if len(st.session_state.threads) > 1:
                if st.button("🗑️", key=f"delete_{thread_id}", help="Delete Thread"):
                    delete_thread_sync(thread_id)

def _show_thread_history_sync(thread_id: int, thread_data: dict):
    """Display thread history in sidebar synchronously."""
    # Show UI messages instead of workflow history for now
    st.session_state[f"show_history_{thread_id}"] = thread_data.get('messages', [])
