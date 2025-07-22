from langgraph.graph import MessagesState

from pydantic import BaseModel
from typing import Literal

class State(MessagesState):
    user_query: str # user query
    agent_name : str # name of the agent
    agent_output : str # output of the agent

class SupervisorAgentOutput(BaseModel):
    agent_name: Literal['TEXT_TO_SQL', 'RAG', 'MISLEADING']