"""
State definition for Text-to-SQL workflow.
"""

from typing import TypedDict, List, Optional, Any
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState


class State(MessagesState):
    """
    State for Text-to-SQL agent workflow.
    
    This state inherits from MessagesState to properly handle message history
    and adds SQL-specific fields for the workflow.
    """
    
    # User input
    user_query: str
    
    # SQL-specific state
    sql_query: Optional[str]
    query_results: Optional[Any]
    
    # Final output
    model_output: Optional[str]
    
    # Additional metadata
    error_message: Optional[str]
    success: Optional[bool]