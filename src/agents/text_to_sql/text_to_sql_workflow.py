import os
import asyncio
from typing import Any, Dict, List

from langchain_core.messages.tool import ToolMessage
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.utils import config
from src.utils.llm_adapter import LLMAdapter
from src.utils.logger import get_logger
from src.data.prompts.text_to_sql_prompt import system_prompt, user_prompt
from src.agents.text_to_sql.test_to_sql_state import State  # Using the fixed State
from src.agents.text_to_sql.text_to_sql_tools import initialize_sql_tools, get_sql_tools


logger = get_logger(__name__)


class TextToSQLWorkflow:
    """
    Text-to-SQL agent using LangGraph and SQL database tools.
    Converts natural language queries to SQL and executes them against a SQLite database.
    """

    def __init__(self, database_path: str):
        """
        Initialize the Text-to-SQL workflow.

        Args:
            database_path: Path to the SQLite database file
        """
        self.database_path = database_path
        self.llm_client = LLMAdapter(model_name=config.GROQ_MODEL_NAME, temperature=0.0)

        # Initialize SQL tools with the LLM for advanced query checking
        initialize_sql_tools(database_path, self.llm_client.client)

        # Get all SQL tools
        self.sql_tools = get_sql_tools()

        # Bind tools to LLM
        self.llm_with_tools = self.llm_client.client.bind_tools(tools=self.sql_tools)

        # Create tool node
        self.tool_node = ToolNode(tools=self.sql_tools)

    async def sql_agent_node(self, state: State) -> Dict[str, Any]:
        """
        Main SQL agent node that processes user queries and generates SQL.
        """
        try:
            user_query = state["user_query"]
            messages = state["messages"]

            # Check if we have tool messages to process
            has_tool_responses = any(isinstance(msg, ToolMessage) for msg in messages)
            
            if has_tool_responses and len(messages) > 0:
                logger.debug("Processing tool response and generating final answer")
                
                # The messages already contain the conversation history
                # Just invoke with the current messages
                llm_response = await self.llm_with_tools.ainvoke(messages)
                
                return {
                    "messages": [llm_response],  # LangGraph will automatically append this
                    "model_output": llm_response.content,
                }

            logger.debug("Generating initial SQL response for query: %s", user_query)

            # If no messages exist or no tool responses, start the conversation
            if not messages:
                # Create initial conversation
                conversation_messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt.format(user_query=user_query)),
                ]
            else:
                # Use existing messages
                conversation_messages = messages

            llm_response = await self.llm_with_tools.ainvoke(conversation_messages)

            return {
                "messages": [llm_response],  # LangGraph will automatically append this
                "user_query": user_query
            }

        except Exception as exc:
            logger.exception("Error in SQL agent node")
            raise RuntimeError(f"SQL agent error: {exc}") from exc

    def build_graph(self) -> StateGraph:
        """
        Build and compile the Text-to-SQL StateGraph.

        Returns:
            Compiled StateGraph for text-to-SQL processing
        """
        graph = StateGraph(State)

        # Add nodes
        graph.add_node("sql_agent", self.sql_agent_node)
        graph.add_node("tool_execution", self.tool_node)

        # Add edges
        graph.add_edge(START, "sql_agent")

        # Conditional edge from sql_agent
        graph.add_conditional_edges(
            "sql_agent",
            tools_condition,
            {"tools": "tool_execution", END: END},
        )

        # Edge from tool_execution back to sql_agent
        graph.add_edge("tool_execution", "sql_agent")

        # Compile the graph
        compiled = graph.compile()
        logger.info("Text-to-SQL StateGraph compiled successfully")
        return compiled

    async def run_query(self, user_query: str) -> Dict[str, Any]:
        """
        Run a single text-to-SQL query.

        Args:
            user_query: Natural language query from user

        Returns:
            Dictionary containing the results and metadata
        """
        try:
            graph = self.build_graph()

            logger.info("Processing query: %s", user_query)

            # Initialize state with system and user messages
            initial_state = {
                "user_query": user_query,
                "messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt.format(user_query=user_query)),
                ]
            }

            final_state = None
            async for step in graph.astream(initial_state):
                logger.debug("Graph step: %s", step)
                final_state = step

            # Extract final results
            if final_state:
                for node_name, node_state in final_state.items():
                    if "model_output" in node_state:
                        return {
                            "user_query": user_query,
                            "response": node_state["model_output"],
                            "sql_query": node_state.get("sql_query"),
                            "query_results": node_state.get("query_results"),
                            "success": True,
                        }

            return {
                "user_query": user_query,
                "response": "No response generated",
                "success": False,
            }

        except Exception as e:
            logger.error("Error running query: %s", e)
            return {
                "user_query": user_query,
                "response": f"Error processing query: {str(e)}",
                "success": False,
            }

    async def chat_loop(self):
        """
        Interactive chat loop for testing the Text-to-SQL agent.
        """
        print("🤖 Text-to-SQL Agent Ready!")
        print("💾 Database:", self.database_path)
        print("💬 Type your questions in natural language")
        print("📝 Type 'quit' to exit\n")

        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                if not user_input:
                    continue

                print("🔄 Processing...")
                result = await self.run_query(user_input)

                print(f"\n🤖 Assistant: {result['response']}")

                if result.get("sql_query"):
                    print(f"🔍 SQL Query: {result['sql_query']}")

                if result.get("query_results"):
                    print(f"📊 Results: {result['query_results']}")

                print("-" * 50)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error("Error in chat loop: %s", e)
                print(f"❌ Error: {e}")


# Standalone usage functions for flexibility
async def run_single_query(database_path: str, query: str) -> Dict[str, Any]:
    """
    Run a single text-to-SQL query without interactive loop.

    Args:
        database_path: Path to SQLite database
        query: Natural language query

    Returns:
        Query results and metadata
    """
    workflow = TextToSQLWorkflow(database_path)
    return await workflow.run_query(query)


async def start_interactive_session(database_path: str):
    """
    Start an interactive text-to-SQL session.

    Args:
        database_path: Path to SQLite database
    """
    workflow = TextToSQLWorkflow(database_path)
    await workflow.chat_loop()


if __name__ == "__main__":

    async def main():
        try:
            # Get database path from user or use default
            db_path = input(
                "Enter database path (or press Enter for 'database.db'): "
            ).strip()
            if not db_path:
                db_path = "database.db"

            # Check if database exists
            if not os.path.exists(db_path):
                logger.error("Database file not found: %s", db_path)
                print(f"❌ Database file not found: {db_path}")
                return

            # Choose mode
            mode = input("Choose mode: [1] Interactive chat [2] Single query: ").strip()

            if mode == "2":
                query = input("Enter your query: ").strip()
                if query:
                    logger.info("Running single query: %s", query)
                    result = await run_single_query(db_path, query)
                    print("\n" + "=" * 50)
                    print(f"Query: {result['user_query']}")
                    print(f"Response: {result['response']}")
                    if result.get("sql_query"):
                        print(f"SQL: {result['sql_query']}")
                    if result.get("query_results"):
                        print(f"Results: {result['query_results']}")
                    print("=" * 50)
            else:
                # Default to interactive mode
                logger.info("Starting interactive Text-to-SQL session")
                await start_interactive_session(db_path)

        except RuntimeError as e:
            logger.error("Fatal Text-to-SQL error: %s", e)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error("Unexpected error: %s", e)
        finally:
            logger.info("Exiting TextToSQLWorkflow")

    asyncio.run(main())