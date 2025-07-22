import asyncio
from src.agents.graph import SupervisorWorkflow  # Adjust import path

def initialize_workflow_sync(thread_id: int):
    """Initialize SupervisorWorkflow synchronously."""
    return asyncio.run(initialize_workflow(thread_id))

async def initialize_workflow(thread_id: int):
    """Initialize SupervisorWorkflow for a thread."""
    workflow = SupervisorWorkflow(thread_id=thread_id)
    graph = workflow.build_graph()
    return workflow, graph
