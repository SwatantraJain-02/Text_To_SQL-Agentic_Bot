"""
RAG agent node implementation.
"""

from typing import Any, Dict, List

from langchain_core.messages.tool import ToolMessage

from src.agents.rag.rag_state import State
from src.utils.llm_adapter import LLMAdapter
from src.utils import config
from src.utils.logger import get_logger
from src.agents.rag.rag_tools import rag_tools
from src.data.prompts.rag_prompts import system_prompt, user_prompt

logger = get_logger(__name__)

llm_client = LLMAdapter(model_name=config.GROQ_MODEL_NAME, temperature=0.0)
llm_with_tools = llm_client.client.bind_tools(tools=rag_tools)


def rag_agent(state: State) -> Dict[str, Any]:
    """
    Orchestrate RAG agent interactions: generate initial responses and handle tool results.

    Args:
        state: The RAG agent state containing user query and message history.

    Returns:
        A dictionary with keys:
          - 'messages': List of LLM messages.
          - 'model_output': (optional) String content of the last LLM response.
    """
    try:
        logger.info("Starting RAG agent processing")
        user_query = state["user_query"]
        logger.debug("Received user query: %s", user_query)

        messages = state["messages"]
        if messages and isinstance(messages[-1], ToolMessage):
            logger.info("Processing tool agent response")
            try:
                llm_response = llm_with_tools.invoke(messages)
                logger.info("Generated LLM response after tool call")
                return {
                    "messages": [llm_response],
                    "model_output": llm_response.content,
                }
            except Exception:
                logger.exception("Error generating LLM response after tool call")
                raise

        logger.info("Generating initial LLM response")
        conversation: List[Any] = [
            ("system", system_prompt),
            ("user", user_prompt.format(user_query=user_query)),
        ]

        try:
            response = llm_with_tools.invoke(conversation)
            logger.info("Generated initial LLM response")
            return {"messages": [response]}
        except Exception:
            logger.exception("Error generating initial LLM response")
            logger.debug("System prompt: %s", system_prompt)
            logger.debug("User prompt: %s", user_prompt.format(user_query=user_query))
            raise

    except Exception:
        logger.exception("Error in RAG agent")
        raise
