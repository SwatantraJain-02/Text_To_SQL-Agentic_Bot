from langgraph.graph import MessagesState
from typing import List

class State(MessagesState):
    model_output: str
    user_query :str
