from mcp.server.fastmcp import FastMCP
from langchain_core.messages import SystemMessage
from src.agent import get_agent, SYSTEM_PROMPT
from src.orchestrator import get_orchestrator_graph
from langchain_core.messages import HumanMessage
import asyncio

# Initialize FastMCP server
mcp = FastMCP("College ROI Agents")

@mcp.tool()
async def get_college_tuition(college_name: str) -> str:
    """
    Get tuition information for a specific college.
    """
    try:
        agent = get_agent()
    except Exception as e:
        return f"Error initializing agent: {str(e)}"

    print(f"Researching tuition for: {college_name}...")
    
    inputs = {"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        ("user", f"Find the per-year tuition cost for {college_name}")
    ]}
    
    try:
        # Since agent.invoke is synchronous (based on previous usage in server.py), 
        # we can wrap it if needed or just call it directly.
        # But FastMCP handles sync functions too. 
        # Let's check if agent.invoke is async or sync. 
        # In server.py it was called synchronously: result = agent.invoke(inputs)
        # However, we are in an async function here. 
        # To avoid blocking the event loop, we should run it in an executor.
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, agent.invoke, inputs)
        
        # The last message is the result from the assistant
        full_content = result["messages"][-1].content
        
        return full_content
    except Exception as e:
        return f"Error during agent execution: {str(e)}"

@mcp.tool()
async def get_personalized_cost(college_name: str, family_contribution: int, financial_aid: int) -> str:
    """
    Get a personalized cost estimate for a college, accounting for family contribution and financial aid.
    """
    try:
        agent = get_agent()
    except Exception as e:
        return f"Error initializing agent: {str(e)}"

    print(f"Calculating personalized cost for: {college_name}...")
    
    # We use the same system prompt but a more specific user prompt
    prompt = f"""Find the per-year tuition cost for {college_name}. 
    Then, using the following financial details:
    - Family Contribution: ${family_contribution}
    - Expected Financial Aid: ${financial_aid}
    
    Calculate:
    1. The Net Price (Total Cost - Financial Aid)
    2. The Remaining Gap (Net Price - Family Contribution)
    
    Provide a clear breakdown of the costs, aid, and what the family still needs to cover (or if they have a surplus).
    """

    inputs = {"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        ("user", prompt)
    ]}
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, agent.invoke, inputs)
        
        full_content = result["messages"][-1].content
        return full_content
    except Exception as e:
        return f"Error during agent execution: {str(e)}"

@mcp.tool()
async def chat_with_orchestrator(message: str, user_id: str = "default_user") -> str:
    """
    Chat with the College ROI Orchestrator. 
    It maintains state about your researched colleges and validated info.
    """
    try:
        graph = get_orchestrator_graph()
        config = {"configurable": {"thread_id": user_id}}
        
        # In a real app, we'd fetch the existing state or let LangGraph handle it via thread_id
        # We just need to pass the new message
        inputs = {"messages": [HumanMessage(content=message)]}
        
        # We use a loop for the graph since it might have multiple steps (orchestrator -> researcher)
        # But we'll just gather the final output for the MCP response
        result = None
        
        # Run the graph
        loop = asyncio.get_event_loop()
        
        # We'll use graph.ainvoke if it's async-friendly or run graph.invoke in executor
        # Since SqliteSaver might block, executor is safer for basic implementation
        def run_graph():
            # For a simpler response, we can just use invoke
            return graph.invoke(inputs, config=config)
            
        result = await loop.run_in_executor(None, run_graph)
        
        # Return the last AI message
        return result["messages"][-1].content
        
    except Exception as e:
        return f"Error in orchestrator: {str(e)}"

if __name__ == "__main__":
    mcp.run()
