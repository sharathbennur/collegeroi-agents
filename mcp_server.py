from mcp.server.fastmcp import FastMCP
from langchain_core.messages import SystemMessage
from src.agent import get_agent, SYSTEM_PROMPT
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

if __name__ == "__main__":
    mcp.run()
