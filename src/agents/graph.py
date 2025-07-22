import os
import asyncio
import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.utils import config
from src.utils.llm_adapter import LLMAdapter
from src.utils.logger import get_logger
from src.data.prompts.supervisor_prompt import system_prompt, user_prompt
from src.agents.state import State, SupervisorAgentOutput
from src.agents.text_to_sql.text_to_sql_workflow import TextToSQLWorkflow
from src.agents.rag.rag_workflow import RAGWorkflow
from src.agents.misleading.misleading_workflow import MisleadingWorkflow

logger = get_logger(__name__)


class SupervisorWorkflow:
    """
    Supervisor agent using LangGraph to route queries to appropriate specialized agents with memory support.
    """

    def __init__(self, thread_id: int = 1):
        self.llm_client = LLMAdapter(model_name=config.GROQ_MODEL_NAME, temperature=0.0)
        self.llm_client_with_structured_output = self.llm_client.client.with_structured_output(SupervisorAgentOutput)
        
        # Initialize memory saver for persistent conversation history
        self.memory = MemorySaver()
        self.thread_id = str(thread_id)  # Convert to string for internal use

        # Intitialising the database path
        DB_PATH = config.DB_PATH
        # Initialize specialized workflows
        self.text2sql_workflow = TextToSQLWorkflow(DB_PATH)
        self.rag_workflow = RAGWorkflow()
        self.misleading_workflow = MisleadingWorkflow()

        # Compile specialized graphs with memory
        self.text2sql_graph: StateGraph = self.text2sql_workflow.build_graph()
        self.rag_graph: StateGraph = self.rag_workflow.build_graph()
        self.misleading_graph: StateGraph = self.misleading_workflow.build_graph()

    def get_config(self) -> Dict[str, Any]:
        """Get configuration with thread ID for memory persistence."""
        return {"configurable": {"thread_id": self.thread_id}}

    async def supervisor_agent_node(self, state: State) -> Dict[str, Any]:
        """
        Supervisor node that analyzes user query and selects appropriate agent.
        Maintains conversation history in memory.
        """
        try:
            user_query = state["user_query"]
            conversation_history = state.get("messages", [])
            
            logger.info(
                f"------------------------------NEW USER QUERY------------------------------: {user_query}"
            )

            user_question = HumanMessage(content=user_query)

            # Handle special history request
            if user_query == "get_history":
                return {
                    "messages": conversation_history,
                    "agent_output": f"Conversation history contains {len(conversation_history)} messages."
                }

            logger.info("Starting supervisor agent processing")
            logger.debug(f"Processing user query: {user_query}")
            logger.debug(f"Current conversation history length: {len(conversation_history)}")

            # Create context-aware prompt including recent conversation history
            context_messages = []
            if conversation_history:
                # Include last few messages for context (limit to prevent token overflow)
                recent_messages = conversation_history[-6:]  # Last 3 exchanges
                context_str = "\n".join([
                    f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
                    for msg in recent_messages
                ])
                context_messages.append(("system", f"Recent conversation context:\n{context_str}\n\n{system_prompt}"))
            else:
                context_messages.append(("system", system_prompt))

            context_messages.append(("user", user_prompt.format(user_query=user_query)))

            # Generate agent selection response
            response: SupervisorAgentOutput = await self.llm_client_with_structured_output.ainvoke(
                context_messages
            )
            
            agent_name = response.agent_name
            logger.info(f"Selected agent: {agent_name}")

            # Update conversation history
            updated_messages = conversation_history + [user_question]

            return {
                "agent_name": agent_name, 
                "messages": updated_messages,
                "supervisor_response": response
            }

        except Exception as e:
            logger.error(f"Error in supervisor agent: {str(e)}")
            raise RuntimeError(f"Supervisor agent error: {e}") from e

    async def text2sql_agent_node(self, state: State) -> Dict[str, Any]:
        """
        Text2SQL agent node that processes database queries with conversation context.
        """
        try:
            logger.info("Starting text2sql agent processing")
            user_query = state["user_query"]
            conversation_history = state.get("messages", [])
            
            logger.debug(f"Processing user query: {user_query}")

            # Pass conversation history to the text2sql workflow
            text2sql_input = {
                "user_query": user_query,
                "messages": conversation_history
            }

            text2sql_output = await self.text2sql_graph.ainvoke(
                text2sql_input, self.get_config()
            )
            logger.info("Successfully processed text2sql request")

            # Create AI response message
            ai_response = AIMessage(content=text2sql_output.get("model_output", ""))
            updated_messages = conversation_history + [ai_response]

            return {
                "agent_name": "text2sql",
                "messages": updated_messages,
                "agent_output": text2sql_output.get("model_output", ""),
            }

        except Exception as e:
            logger.error(f"Error in text2sql agent: {str(e)}")
            raise RuntimeError(f"Text2SQL agent error: {e}") from e

    async def rag_agent_node(self, state: State) -> Dict[str, Any]:
        """
        RAG agent node that processes document retrieval queries with conversation context.
        """
        try:
            logger.info("Starting RAG agent processing")
            user_query = state["user_query"]
            conversation_history = state.get("messages", [])
            
            logger.debug(f"Processing user query: {user_query}")

            # Pass conversation history to the RAG workflow
            rag_input = {
                "user_query": user_query,
                "messages": conversation_history
            }

            rag_output = await self.rag_graph.ainvoke(
                rag_input, self.get_config()
            )
            logger.info("Successfully processed RAG request")

            # Create AI response message
            ai_response = AIMessage(content=rag_output.get("model_output", ""))
            updated_messages = conversation_history + [ai_response]

            return {
                "agent_name": "rag",
                "messages": updated_messages,
                "agent_output": rag_output.get("model_output", ""),
            }

        except Exception as e:
            logger.error(f"Error in RAG agent: {str(e)}")
            raise RuntimeError(f"RAG agent error: {e}") from e

    async def misleading_agent_node(self, state: State) -> Dict[str, Any]:
        """
        Misleading agent node that handles queries outside the scope of available agents.
        """
        try:
            logger.info("Starting misleading agent processing")
            user_query = state["user_query"]
            conversation_history = state.get("messages", [])
            
            logger.debug(f"Processing user query: {user_query}")

            # Pass conversation history to the misleading workflow
            misleading_input = {
                "user_query": user_query,
                "messages": conversation_history
            }

            # Invoke the misleading agent workflow
            misleading_output = await self.misleading_graph.ainvoke(
                misleading_input, self.get_config()
            )
            logger.info("Successfully processed misleading request")

            # Create AI response message
            ai_response = AIMessage(content=misleading_output.get("model_output", ""))
            updated_messages = conversation_history + [ai_response]

            return {
                "agent_name": "misleading",
                "messages": updated_messages,
                "agent_output": misleading_output.get("model_output", ""),
            }

        except Exception as e:
            logger.error(f"Error in misleading agent: {str(e)}")
            raise RuntimeError(f"Misleading agent error: {e}") from e

    def agent_selection_condition(self, state: State) -> str:
        """
        Conditional logic for routing to appropriate agent based on supervisor's selection.
        """
        agent_name = state.get("agent_name", "").upper()

        routing_map = {
            "TEXT_TO_SQL": "text_to_sql",
            "RAG": "rag",
            "MISLEADING": "misleading",
        }

        return routing_map.get(agent_name, "misleading")

    def build_graph(self) -> StateGraph:
        """
        Build and compile the supervisor workflow graph with memory support.
        """
        graph = StateGraph(State)

        # Add nodes
        graph.add_node("supervisor", self.supervisor_agent_node)
        graph.add_node("text_to_sql", self.text2sql_agent_node)
        graph.add_node("rag", self.rag_agent_node)
        graph.add_node("misleading", self.misleading_agent_node)

        # Add edges
        graph.add_edge(START, "supervisor")

        # Conditional edges from supervisor
        graph.add_conditional_edges(
            "supervisor",
            self.agent_selection_condition,
            {"text_to_sql": "text_to_sql", "rag": "rag", "misleading": "misleading"},
        )

        # All agent nodes end the workflow
        graph.add_edge("text_to_sql", END)
        graph.add_edge("rag", END)
        graph.add_edge("misleading", END)

        # Compile with memory support
        compiled = graph.compile(checkpointer=self.memory)
        logger.info("Supervisor StateGraph compiled successfully with memory support")
        return compiled

    async def clear_memory(self):
        """Clear the conversation memory for the current thread."""
        try:
            # Clear memory for current thread
            await self.memory.aput(self.get_config(), None, {})
            logger.info(f"Memory cleared for thread: {self.thread_id}")
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")

    async def get_conversation_history(self) -> List[Any]:
        """Retrieve conversation history from memory."""
        try:
            checkpoint = await self.memory.aget(self.get_config())
            if checkpoint and checkpoint.channel_values:
                return checkpoint.channel_values.get("messages", [])
            return []
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []


if __name__ == "__main__":

    async def main():
        try:
            # Initialize with a specific thread ID for this session
            thread_id = int(asyncio.get_event_loop().time())
            wf = SupervisorWorkflow(thread_id=thread_id)
            graph = wf.build_graph()

            print(f"Starting SupervisorWorkflow with thread ID: {thread_id}")
            print("Available commands:")
            print("- 'history': Show conversation history")
            print("- 'clear': Clear conversation memory")
            print("- 'quit'/'exit'/'q': Exit the program")
            print("-" * 50)

            while True:
                query = input("\nEnter your query: ").strip()
                
                if query.lower() in ["quit", "exit", "q"]:
                    break
                elif query.lower() == "clear":
                    await wf.clear_memory()
                    print("✓ Memory cleared successfully")
                    continue
                elif query.lower() == "history":
                    history = await wf.get_conversation_history()
                    if history:
                        print(f"\n📚 Conversation History ({len(history)} messages):")
                        for i, msg in enumerate(history[-10:], 1):  # Show last 10 messages
                            msg_type = "🧑 User" if isinstance(msg, HumanMessage) else "🤖 Assistant"
                            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                            print(f"{i}. {msg_type}: {content}")
                    else:
                        print("📭 No conversation history found")
                    continue

                if not query:
                    continue

                logger.info("Running Supervisor graph for query: %s", query)

                try:
                    # Stream the workflow execution
                    final_output = None
                    async for step in graph.astream(
                        {"user_query": query}, 
                        wf.get_config()
                    ):
                        print(f"\n🔄 Processing step: {list(step.keys())}")
                        
                        # Extract and display results
                        for node_name, node_data in step.items():
                            if "agent_name" in node_data:
                                print(f"🎯 Selected Agent: {node_data['agent_name']}")
                            if "agent_output" in node_data:
                                final_output = node_data['agent_output']

                    # Display final result
                    if final_output:
                        print(f"\n✅ Final Response:")
                        print("-" * 30)
                        print(final_output)
                        print("-" * 30)

                except Exception as e:
                    print(f"❌ Error processing query: {str(e)}")
                    logger.error(f"Error in workflow execution: {str(e)}")

        except RuntimeError as e:
            logger.error("Fatal Supervisor error: %s", e)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        finally:
            logger.info("Exiting SupervisorWorkflow")

    asyncio.run(main())