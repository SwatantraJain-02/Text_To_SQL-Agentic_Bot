import os
from typing import List, Any

from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.prebuilt import ToolNode

from src.utils import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_database_retrieval_tool() -> Any:
    """
    Factory to create a standalone LangChain tool function for document retrieval.
    Avoids 'self' binding issues with class methods.
    """
    @tool
    def database_retrieval(query: str) -> List[str]:
        """
        Retrieve relevant documents from the vector database using Maximal Marginal
        Relevance (MMR).

        Args:
            query: The input query string.

        Returns:
            A list of document page contents.

        Raises:
            RuntimeError: If the vector database directory is missing or another error occurs.
        """
        try:
            if not os.path.isdir(config.DB_DIRECTORY):
                raise RuntimeError(f"Vector DB not found: {config.DB_DIRECTORY}")

            embedder = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
            vectorstore = Chroma(
                persist_directory=config.DB_DIRECTORY,
                embedding_function=embedder,
                collection_name=config.COLLECTION_NAME,
            )
            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 5, "fetch_k": 50},
            )
            docs = retriever.get_relevant_documents(query)
            return [doc.page_content for doc in docs]
        except Exception as exc:
            logger.exception("Retrieval tool failed")
            raise RuntimeError(f"Tool error: {exc}") from exc

    return database_retrieval
