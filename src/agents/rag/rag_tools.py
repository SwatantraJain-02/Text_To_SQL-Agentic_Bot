import os
from typing import List

from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.prebuilt import ToolNode

from src.utils import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


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
        # Validate the database directory
        if not os.path.isdir(config.DB_DIRECTORY):
            msg = f"Vector database directory not found: {config.DB_DIRECTORY}"
            logger.error(msg)
            raise RuntimeError(msg)

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

        documents = retriever.get_relevant_documents(query)
        if not documents:
            logger.warning("No documents found for query: %s", query)
            return []

        results = [doc.page_content for doc in documents]
        logger.info("Retrieved %d documents for query: %s", len(results), query)
        logger.debug("Document contents: %s", results)
        return results

    except Exception:
        logger.exception("Failed to retrieve documents for query: %s", query)
        raise


# Expose for RAG agent
rag_tools = [database_retrieval]
tool_node = ToolNode(tools=rag_tools)
