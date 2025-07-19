"""
RAG agent StateGraph assembly.
"""

from typing import Dict

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.utils import config
from src.utils.llm_adapter import LLMAdapter
from src.utils.logger import get_logger


from src.agents.rag.rag_state import State
from src.agents.rag.rag_nodes import rag_agent
from src.agents.rag.rag_tools import tool_node, rag_tools

logger = get_logger(__name__)

# Initialize LLM client and bind tools for RAG
llm_client = LLMAdapter(model_name=config.GROQ_MODEL_NAME, temperature=0.0)
llm_with_tools = llm_client.client.bind_tools(tools=rag_tools)

# Define node identifiers
NODE_RAG_AGENT = "rag_agent"
NODE_TOOL_EXECUTION = "tool_execution"

# Build the RAG processing graph
graph_builder = StateGraph(State)
graph_builder.add_node(NODE_RAG_AGENT, rag_agent)
graph_builder.add_node(NODE_TOOL_EXECUTION, tool_node)

graph_builder.add_edge(START, NODE_RAG_AGENT)
graph_builder.add_conditional_edges(
    NODE_RAG_AGENT,
    tools_condition,
    {"tools": NODE_TOOL_EXECUTION, END: END},
)
graph_builder.add_edge(NODE_TOOL_EXECUTION, NODE_RAG_AGENT)

# Compile final application graph
app_rag_agent = graph_builder.compile()
logger.info(
    "Compiled RAG StateGraph with nodes [%s, %s]", NODE_RAG_AGENT, NODE_TOOL_EXECUTION
)

import asyncio

if __name__ == "__main__":
    query = input("Enter your query: ").strip()

    async def run():
        print("\n--- Running Graph ---\n")
        async for step in app_rag_agent.astream({'user_query': query}):
            print("Step:", step)

    asyncio.run(run())

