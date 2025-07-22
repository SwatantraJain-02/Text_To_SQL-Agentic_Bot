import streamlit as st
import asyncio
import time
import re
from datetime import datetime

def parse_response_with_thinking(response: str):
    """Parse response to separate thinking and actual response."""
    # Pattern to match <think>...</think> tags
    think_pattern = r'<think>(.*?)</think>'
    
    # Extract thinking content
    think_match = re.search(think_pattern, response, re.DOTALL)
    thinking_content = think_match.group(1).strip() if think_match else None
    
    # Remove thinking tags from the main response
    cleaned_response = re.sub(think_pattern, '', response, flags=re.DOTALL).strip()
    
    return thinking_content, cleaned_response

def render_chat():
    """Render the main chat interface."""
    current_thread_id = st.session_state.current_thread_id
    current_thread = st.session_state.threads[current_thread_id]
    
    # Display thread info
    created_time = datetime.fromtimestamp(current_thread['created_at']) if isinstance(current_thread['created_at'], (int, float)) else current_thread['created_at']
    st.title(f"💬 {current_thread['title']}")
    st.caption(f"Thread ID: {current_thread_id} | Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Add toggle for showing thinking process
    show_thinking = st.checkbox("🧠 Show AI Thinking Process", value=False, key=f"show_thinking_{current_thread_id}")
    
    # Display messages
    for message in current_thread['messages']:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "thinking" in message:
                # Display thinking process if enabled
                if show_thinking and message.get("thinking"):
                    with st.expander("🤔 AI Thinking Process", expanded=False):
                        st.markdown(f"*{message['thinking']}*")
                
                # Display the main response
                st.markdown(message["content"])
            else:
                st.markdown(message["content"])
    
    # Handle chat input
    _handle_chat_input(current_thread, show_thinking)

def _handle_chat_input(current_thread: dict, show_thinking: bool):
    """Handle user input and generate responses."""
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        current_thread['messages'].append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Initialize workflow if needed (lazy loading)
        if current_thread['workflow'] is None:
            with st.spinner("Initializing workflow..."):
                try:
                    from frontend.utils.workflow_handler import initialize_workflow_sync
                    workflow, graph = initialize_workflow_sync(st.session_state.current_thread_id)
                    current_thread['workflow'] = workflow
                    current_thread['graph'] = graph
                except Exception as e:
                    st.error(f"Error initializing workflow: {str(e)}")
                    return
        
        # Generate response
        workflow = current_thread['workflow']
        graph = current_thread['graph']
        
        with st.chat_message("assistant"):
            with st.spinner("Processing your query..."):
                try:
                    response = asyncio.run(process_query_async(prompt, workflow, graph))
                    
                    if response:
                        # Parse the response to separate thinking and content
                        thinking_content, cleaned_response = parse_response_with_thinking(response)
                        
                        # Display thinking process if available and enabled
                        if thinking_content and show_thinking:
                            with st.expander("🤔 AI Thinking Process", expanded=False):
                                st.markdown(f"*{thinking_content}*")
                        
                        # Display the main response
                        st.markdown(cleaned_response)
                        
                        # Store both thinking and response in message history
                        message_data = {
                            "role": "assistant", 
                            "content": cleaned_response
                        }
                        if thinking_content:
                            message_data["thinking"] = thinking_content
                        
                        current_thread['messages'].append(message_data)
                        
                        # Update thread title for first exchange
                        if len(current_thread['messages']) == 2:
                            current_thread['title'] = prompt[:30] + "..." if len(prompt) > 30 else prompt
                        
                        st.rerun()
                except Exception as e:
                    error_msg = f"Error processing query: {str(e)}"
                    st.error(error_msg)
                    current_thread['messages'].append({"role": "assistant", "content": error_msg})

async def process_query_async(query: str, workflow, graph):
    """Process a user query through the SupervisorWorkflow."""
    try:
        config = workflow.get_config()
        final_output = None
        
        async for step in graph.astream({"user_query": query}, config):
            for node_name, node_data in step.items():
                if "agent_output" in node_data:
                    final_output = node_data['agent_output']
        
        return final_output or "No response generated"
        
    except Exception as e:
        return f"Error: {str(e)}"
