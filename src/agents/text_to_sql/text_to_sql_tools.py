"""
SQL Database Tools for LangGraph - SQLite Implementation
This module provides 4 SQL database tools compatible with LangGraph's ToolNode.
"""

from typing import Any, Dict, List, Optional, Union
import sqlite3
from langchain_core.tools import tool
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
import re

from src.utils.logger import get_logger

logger = get_logger(__name__)


# Query Checker Prompt Template
QUERY_CHECKER = """
{query}
Double check the {dialect} query above for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatches in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns that exist in the tables
- Proper SQL {dialect} syntax

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final SQL query only.
"""


class SQLTools:
    """Container class for SQL database tools."""

    def __init__(self, database_path: str, llm: Optional[BaseLanguageModel] = None):
        """
        Initialize SQL Tools with SQLite database.

        Args:
            database_path: Path to the SQLite database file
            llm: Language model for query checking (optional)
        """
        self.database_path = database_path
        self.db = SQLDatabase.from_uri(f"sqlite:///{database_path}")
        self.llm = llm

        # Initialize LLM chain for query checker if LLM is provided
        if self.llm:
            # Using the new RunnableSequence approach with proper invoke method
            self.prompt = PromptTemplate(
                template=QUERY_CHECKER, 
                input_variables=["dialect", "query"]
            )
            # Create the chain with output parser
            self.llm_chain = self.prompt | self.llm | StrOutputParser()
        else:
            self.llm_chain = None


# Global instance to be set by user
_sql_tools_instance: Optional[SQLTools] = None


def initialize_sql_tools(database_path: str, llm: Optional[BaseLanguageModel] = None):
    """
    Initialize the global SQL tools instance.

    Args:
        database_path: Path to the SQLite database file
        llm: Language model for query checking (optional)
    """
    logger.info(f"Initializing SQLTools with database {database_path}")
    try:
        global _sql_tools_instance
        _sql_tools_instance = SQLTools(database_path, llm)
        logger.info("SQLTools initialized successfully")
    except Exception as e:
        logger.error(
            f"Failed to initialize SQLTools for {database_path}: {e}", exc_info=True
        )
        raise


def _get_sql_tools() -> SQLTools:
    """Get the global SQL tools instance."""
    if _sql_tools_instance is None:
        raise ValueError(
            "SQL tools not initialized. Call initialize_sql_tools() first."
        )
    return _sql_tools_instance


@tool
def sql_db_query(query: str) -> str:
    """
    Execute a SQL query against the database and get back the result.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.

    Args:
        query: A detailed and correct SQL query.

    Returns:
        Query results or error message.
    """
    logger.info(f"sql_db_query called with query: {query}")
    tools = _get_sql_tools()
    try:
        result = tools.db.run_no_throw(query)
        logger.info(f"sql_db_query result: {result}")
        return str(result)
    except Exception as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        return f"Error executing query: {e}"


@tool
def sql_db_schema(table_names: str) -> str:
    """
    Get the schema and sample rows for the specified SQL tables.

    Args:
        table_names: A comma-separated list of the table names for which to return the schema.
                    Example input: 'table1, table2, table3'

    Returns:
        Schema and sample rows for the specified tables.
    """
    logger.info(f"sql_db_schema called with table_names: {table_names}")
    tools = _get_sql_tools()
    try:
        table_list = [t.strip() for t in table_names.split(",")]
        result = tools.db.get_table_info_no_throw(table_list)
        logger.info(f"sql_db_schema result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting schema for {table_names}: {e}", exc_info=True)
        return f"Error getting schema: {e}"


@tool
def sql_db_list_tables(tool_input: str = "") -> str:
    """
    Input is an empty string, output is a comma-separated list of tables in the database.

    Args:
        tool_input: An empty string (not used)

    Returns:
        Comma-separated list of table names in the database.
    """
    tools = _get_sql_tools()
    try:
        table_names = list(tools.db.get_usable_table_names())
        return ", ".join(table_names)
    except Exception as e:
        return f"Error listing tables: {str(e)}"


@tool
def sql_db_query_checker(query: str) -> str:
    """
    Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a query with sql_db_query!

    Args:
        query: A detailed SQL query to be checked.

    Returns:
        The corrected query or the original query if no issues found.
    """
    tools = _get_sql_tools()

    if tools.llm_chain is None:
        # Simple validation without LLM
        return _simple_query_validation(query, tools.db.dialect)

    try:
        # Use LLM for advanced query checking with the new invoke method
        result = tools.llm_chain.invoke({
            "query": query, 
            "dialect": tools.db.dialect
        })
        
        # Extract just the SQL query from the result if it contains extra text
        result = result.strip()
        
        # If the result contains explanatory text, try to extract just the SQL
        lines = result.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')) or 
                        line.startswith(('select', 'insert', 'update', 'delete', 'create', 'drop', 'alter'))):
                return line
        
        return result
        
    except Exception as e:
        logger.error(f"Error in LLM query checker: {e}", exc_info=True)
        # Fall back to simple validation if LLM fails
        return _simple_query_validation(query, tools.db.dialect)


def _simple_query_validation(query: str, dialect: str) -> str:
    """
    Simple query validation without LLM.
    Checks for basic SQL syntax issues and common mistakes.
    """
    query = query.strip()

    # Basic syntax checks
    if not query:
        return "Error: Empty query"

    if not query.upper().startswith(
        ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")
    ):
        return "Error: Query should start with a valid SQL command"

    # Check for balanced parentheses
    if query.count("(") != query.count(")"):
        return "Error: Unbalanced parentheses in query"

    # Check for balanced quotes
    single_quotes = query.count("'")
    double_quotes = query.count('"')
    if single_quotes % 2 != 0:
        return "Error: Unbalanced single quotes in query"
    if double_quotes % 2 != 0:
        return "Error: Unbalanced double quotes in query"

    # Basic SQLite-specific checks
    if dialect.lower() == "sqlite":
        # SQLite doesn't support RIGHT JOIN
        if re.search(r"\bRIGHT\s+JOIN\b", query.upper()):
            return "Error: SQLite does not support RIGHT JOIN. Use LEFT JOIN instead"

        # SQLite has limited ALTER TABLE support
        if re.search(r"\bALTER\s+TABLE\b.*\bDROP\s+COLUMN\b", query.upper()):
            return "Error: SQLite does not support DROP COLUMN in ALTER TABLE"

    # If no issues found, return original query
    return query


# Convenience function to get all tools
def get_sql_tools() -> List[callable]:
    """
    Get all SQL database tools as a list.

    Returns:
        List of SQL database tools for use with LangGraph ToolNode.
    """
    return [sql_db_query, sql_db_schema, sql_db_list_tables, sql_db_query_checker]


# Example usage:
if __name__ == "__main__":
    # Initialize the tools
    from src.utils.llm_adapter import LLMAdapter
    from src.utils import config

    # Without LLM (basic query validation)
    initialize_sql_tools(
        "L:\RoadMapToSwitch\Text_To_SQL-Agentic_Bot\src\db\showroom_management.db"
    )

    # With LLM (advanced query validation)
    llm = LLMAdapter(model_name=config.GROQ_MODEL_NAME).client
    initialize_sql_tools(
        "L:\RoadMapToSwitch\Text_To_SQL-Agentic_Bot\src\db\showroom_management.db", llm
    )

    # Get tools for LangGraph
    tools = get_sql_tools()

    # Use with LangGraph
    from langgraph.prebuilt import ToolNode

    tool_node = ToolNode(tools)

    # Individual tool usage examples:
    # List tables
    tables = sql_db_list_tables("")
    print(f"Tables: {tables}")

    # Get schema for specific tables
    schema = sql_db_schema("customers, orders")
    print(f"Schema: {schema}")

    # Check a query
    checked_query = sql_db_query_checker("SELECT * FROM customers WHERE id = 1")
    print(f"Checked query: {checked_query}")

    # Execute a query
    result = sql_db_query("SELECT COUNT(*) FROM customers")
    print(f"Query result: {result}")