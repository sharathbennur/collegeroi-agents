from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import SystemMessage
from src.agent import get_agent, SYSTEM_PROMPT
from src.orchestrator import get_orchestrator_graph
from langchain_core.messages import HumanMessage
import uvicorn
import os

app = FastAPI(title="College ROI Agent API", description="API to get college tuition information using an AI agent.")

class CollegeRequest(BaseModel):
    college_name: str

class CollegeResponse(BaseModel):
    college_name: str
    tuition_info: str
    sources: list[str] = []

class OrchestratorRequest(BaseModel):
    message: str
    user_id: str = "default_user"

class OrchestratorResponse(BaseModel):
    response: str
    user_id: str

class PersonalizedCostRequest(BaseModel):
    college_name: str
    family_contribution: int
    financial_aid: int

@app.get("/")
async def root():
    return {"message": "Welcome to the College ROI Agent API. Use /college/{college_name} to get tuition info."}

@app.get("/college/{college_name}", response_model=CollegeResponse)
async def get_college_tuition(college_name: str):
    """
    Get tuition information for a specific college.
    """
    try:
        agent = get_agent()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing agent: {str(e)}")

    print(f"Researching tuition for: {college_name}...")
    
    inputs = {"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        ("user", f"Find the per-year tuition cost for {college_name}")
    ]}
    
    try:
        result = agent.invoke(inputs)
        # The last message is the result from the assistant
        full_content = result["messages"][-1].content
        
        # Parse out sources
        sources = []
        clean_content = full_content
        
        if "SOURCES:" in full_content:
            parts = full_content.split("SOURCES:")
            clean_content = parts[0].strip()
            sources_text = parts[1].strip()
            sources = [line.strip() for line in sources_text.split('\n') if line.strip() and line.strip().startswith('http')]

        return CollegeResponse(college_name=college_name, tuition_info=clean_content, sources=sources)
    except Exception as e:
        print(f"Error during agent execution: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/chat", response_model=OrchestratorResponse)
async def chat_with_orchestrator(request: OrchestratorRequest):
    """
    Stateful chat with the College ROI Orchestrator.
    Manages user session memory and directs research.
    """
    try:
        graph = get_orchestrator_graph()
        config = {"configurable": {"thread_id": request.user_id}}
        
        inputs = {"messages": [HumanMessage(content=request.message)]}
        
        # Invoke the graph
        result = graph.invoke(inputs, config=config)
        
        return OrchestratorResponse(
            response=result["messages"][-1].content,
            user_id=request.user_id
        )
    except Exception as e:
        print(f"Error in orchestrator: {e}")
        raise HTTPException(status_code=500, detail=f"Error in orchestrator: {str(e)}")

@app.post("/personalized-cost")
async def get_personalized_cost(request: PersonalizedCostRequest):
    """
    Get a personalized cost estimate for a college.
    """
    try:
        agent = get_agent()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing agent: {str(e)}")

    prompt = f"""Find the per-year tuition cost for {request.college_name}. 
    Then, using the following financial details:
    - Family Contribution: ${request.family_contribution}
    - Expected Financial Aid: ${request.financial_aid}
    
    Calculate:
    1. The Net Price (Total Cost - Financial Aid)
    2. The Remaining Gap (Net Price - Family Contribution)
    
    Provide a clear breakdown of the costs, aid, and what the family still needs to cover.
    """

    inputs = {"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        ("user", prompt)
    ]}
    
    try:
        result = agent.invoke(inputs)
        return {"response": result["messages"][-1].content}
    except Exception as e:
        print(f"Error during agent execution: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
