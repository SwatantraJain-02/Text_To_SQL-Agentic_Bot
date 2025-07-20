import os
import asyncio
from typing import Any, Dict, List

from langchain_core.messages.tool import ToolMessage
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.utils import config
from src.utils.llm_adapter import LLMAdapter
from src.utils.logger import get_logger
from src.data.prompts.rag_prompts import system_prompt, user_prompt
from src.agents.rag.rag_state import State
from src.agents.rag.rag_tools import create_database_retrieval_tool


logger = get_logger(__name__)


class RAGWorkflow:
    """
    RAG agent using LangGraph, LangChain tools, and vector DB retrieval.
    """

    def __init__(self):
        self.llm_client = LLMAdapter(model_name=config.GROQ_MODEL_NAME, temperature=0.0)
        self.rag_tools = [create_database_retrieval_tool()]
        self.llm_with_tools = self.llm_client.client.bind_tools(tools=self.rag_tools)
        self.tool_node = ToolNode(tools=self.rag_tools)

    async def rag_agent_node(self, state: State) -> Dict[str, Any]:
        try:
            user_query = state["user_query"]
            history = state.get("messages") or []

            if history and isinstance(history[-1], ToolMessage):
                logger.debug("Invoking LLM on tool response")
                llm_response = await self.llm_with_tools.ainvoke(history)
                return {
                    "messages": [llm_response],
                    "model_output": llm_response.content,
                }

            logger.debug("Generating initial response")
            convo = [
                ("system", system_prompt),
                ("user", user_prompt.format(user_query=user_query)),
            ]
            llm_response = await self.llm_with_tools.ainvoke(convo)
            return {"messages": [llm_response]}

        except Exception as exc:
            logger.exception("Error in RAG agent node")
            raise RuntimeError(f"RAG agent error: {exc}") from exc

    def build_graph(self) -> StateGraph:
        graph = StateGraph(State)
        graph.add_node("rag_agent", self.rag_agent_node)
        graph.add_node("tool_execution", self.tool_node)
        graph.add_edge(START, "rag_agent")
        graph.add_conditional_edges(
            "rag_agent",
            tools_condition,
            {"tools": "tool_execution", END: END},
        )
        graph.add_edge("tool_execution", "rag_agent")
        compiled = graph.compile()
        logger.info("RAG StateGraph compiled successfully")
        return compiled


if __name__ == "__main__":
    async def main():
        try:
            wf = RAGWorkflow()
            graph = wf.build_graph()
            query = input("Enter your query: ").strip()
            logger.info("Running RAG graph for query: %s", query)

            async for step in graph.astream({"user_query": query}):
                print("Step:", step)

        except RuntimeError as e:
            logger.error("Fatal RAG error: %s", e)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        finally:
            logger.info("Exiting RAGWorkflow")

    asyncio.run(main())
