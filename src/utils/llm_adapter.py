from typing import List, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage

from . import config
from .logger import get_logger

logger = get_logger(__name__)


class LLMAdapter:
    """
    Adapter for invoking the ChatGroq LLM based on provided prompts and messages.
    """

    def __init__(self, model_name: str, temperature: float = 0.0):
        """
        Initialize the ChatGroq client.
        """
        self.logger = get_logger()
        self.model_name = model_name
        self.temperature = temperature
        try:
            self.logger.info(
                f"Initializing ChatGroq model '{model_name}' with temperature={temperature}"
            )
            self.client = ChatGroq(
                model=model_name, api_key=config.GROQ_API_KEY, temperature=temperature
            )
            self.logger.info(f"ChatGroq model '{model_name}' initialized successfully")
        except Exception as e:
            self.logger.error(
                f"Failed to initialize ChatGroq model '{model_name}': {e}",
                exc_info=True,
            )
            raise

    def invoke(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[BaseMessage]] = None,
    ) -> BaseMessage:
        """
        Invokes the LLM with the given prompts and optional message history.
        """
        full_messages: List[BaseMessage] = []

        if system_prompt:
            self.logger.debug(f"Adding system prompt: {system_prompt}")
            full_messages.append(SystemMessage(content=system_prompt))

        if messages:
            self.logger.debug(f"Extending with {len(messages)} prior message(s)")
            full_messages.extend(messages)

        self.logger.debug(f"Adding user prompt: {user_prompt}")
        full_messages.append(HumanMessage(content=user_prompt))

        try:
            self.logger.info(
                f"Invoking model '{self.model_name}' with {len(full_messages)} message(s)"
            )
            response = self.client.invoke(full_messages)
            self.logger.info(f"Received response of type '{type(response).__name__}'")
            return response
        except Exception as e:
            self.logger.error(
                f"Invocation failed for model '{self.model_name}': {e}", exc_info=True
            )
            raise


if __name__ == "__main__":
    # Simple interactive test harness (no argparse)
    test_logger = get_logger()
    test_logger.info("Starting LLMAdapter test harness")

    model_name = "qwen/qwen3-32b"
    if not model_name:
        test_logger.error("No model name provided; exiting.")
        exit(1)

    system_prompt = (
        "You are a good assistant used to help user in answering their questions."
    )
    if not system_prompt:
        test_logger.error("No system prompt provided; exiting.")
        exit(1)

    user_prompt = "Tell me something about LLMs"
    if not user_prompt:
        test_logger.error("No user prompt provided; exiting.")
        exit(1)

    adapter = LLMAdapter(model_name=model_name, temperature=0.0)
    try:
        response = adapter.invoke(system_prompt=system_prompt,
                                  user_prompt=user_prompt)
        
        test_logger.info("LLM response received successfully")
        # Print out the response content if available
        content = getattr(response, "content", response)
        print(content)
    except Exception:
        test_logger.exception("Error during LLMAdapter invocation")
