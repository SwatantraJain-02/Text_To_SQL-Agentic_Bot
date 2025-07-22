import os
import asyncio
from typing import Any, Dict, List

from langgraph.graph import StateGraph, START, END

from src.utils import config
from src.utils.llm_adapter import LLMAdapter
from src.utils.logger import get_logger
from src.data.prompts.misleading_prompt import system_prompt, user_prompt
from src.agents.misleading.misleading_state import State

logger = get_logger(__name__)


class MisleadingWorkflow:
    """
    Misleading agent using LangGraph workflow pattern.
    """

    def __init__(self):
        self.llm_client = LLMAdapter(model_name=config.GROQ_MODEL_NAME, temperature=0.0)

    async def misleading_agent_node(self, state: State) -> Dict[str, Any]:
        try:
            logger.info("Starting misleading agent processing")
            user_query = state["user_query"]
            messages = state.get("messages", [])

            logger.debug(f"Processing user query: {user_query}")

            # Prepare conversation for LLM
            convo = [
                ("system", system_prompt),
                ("user", user_prompt.format(user_query=user_query)),
            ]

            # Add existing messages if available
            if messages:
                convo.extend(messages)

            response = await self.llm_client.client.ainvoke(convo)

            model_output = response.content
            logger.info(f"Misleading agent output: {model_output}")

            return {"model_output": model_output, "messages": [response]}

        except Exception as exc:
            logger.exception("Error in misleading agent node")
            raise RuntimeError(f"Misleading agent error: {exc}") from exc

    def build_graph(self) -> StateGraph:
        graph = StateGraph(State)
        graph.add_node("misleading_agent", self.misleading_agent_node)
        graph.add_edge(START, "misleading_agent")
        graph.add_edge("misleading_agent", END)

        compiled = graph.compile()
        logger.info("Misleading StateGraph compiled successfully")
        return compiled


if __name__ == "__main__":

    async def main():
        try:
            wf = MisleadingWorkflow()
            graph = wf.build_graph()
            query = input("Enter your query: ").strip()
            logger.info("Running misleading graph for query: %s", query)

            async for step in graph.astream({"user_query": query}):
                print("Step:", step)

        except RuntimeError as e:
            logger.error("Fatal misleading agent error: %s", e)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        finally:
            logger.info("Exiting MisleadingWorkflow")

    asyncio.run(main())
