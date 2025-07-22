import streamlit as st
import asyncio
from datetime import datetime
from frontend.utils.workflow_handler import initialize_workflow

async def create_new_thread():
    """Create a new conversation thread with SupervisorWorkflow."""
    thread_id = int(asyncio.get_event_loop().time())
    st.session_state.thread_counter += 1
    
    workflow, graph = await initialize_workflow(thread_id)
    
    st.session_state.threads[thread_id] = {
        'workflow': workflow,
        'graph': graph,
        'messages': [],
        'created_at': datetime.now(),
        'title': f'Conversation {st.session_state.thread_counter}'
    }
    st.session_state.current_thread_id = thread_id
    st.rerun()

async def delete_thread(thread_id: int):
    """Delete a specific thread."""
    if len(st.session_state.threads) > 1:
        if st.session_state.threads[thread_id]['workflow']:
            try:
                await st.session_state.threads[thread_id]['workflow'].clear_memory()
            except Exception as e:
                st.error(f"Error clearing memory: {str(e)}")
        
        del st.session_state.threads[thread_id]
        st.session_state.current_thread_id = list(st.session_state.threads.keys())[0]
        st.rerun()

async def clear_thread_memory(thread_id: int):
    """Clear memory for a specific thread."""
    thread = st.session_state.threads[thread_id]
    if thread['workflow']:
        try:
            await thread['workflow'].clear_memory()
            thread['messages'] = []
            return True
        except Exception as e:
            st.error(f"Error clearing memory: {str(e)}")
            return False
    return False
