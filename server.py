from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.agent import get_agent, SYSTEM_PROMPT
from src.orchestrator import get_orchestrator_graph, OrchestratorState, orchestrator_node, tuition_node, salary_node, tax_node, cost_of_living_node
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from contextlib import asynccontextmanager
import uvicorn
import os
import json
from fastapi.middleware.cors import CORSMiddleware

# Global config to hold the compiled async graph
async_graph = None
db_conn_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global async_graph, db_conn_manager
    # Initialize the async sqlite connection for LangGraph
    db_conn_manager = AsyncSqliteSaver.from_conn_string("checkpoints.sqlite")
    memory = await db_conn_manager.__aenter__()
    
    workflow = StateGraph(OrchestratorState)
    
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tuition_agent", tuition_node)
    workflow.add_node("salary_agent", salary_node)
    workflow.add_node("tax_agent", tax_node)
    workflow.add_node("cost_of_living_agent", cost_of_living_node)
    
    workflow.add_edge(START, "orchestrator")
    
    def route_orchestrator(state: OrchestratorState):
        last_message = state["messages"][-1].content
        if "[ROUTE: TUITION]" in last_message:
            return "tuition_agent"
        elif "[ROUTE: SALARY]" in last_message:
            return "salary_agent"
        elif "[ROUTE: TAX]" in last_message:
            return "tax_agent"
        elif "[ROUTE: COST_OF_LIVING]" in last_message:
            return "cost_of_living_agent"
        return END

    workflow.add_conditional_edges("orchestrator", route_orchestrator)
    
    workflow.add_edge("tuition_agent", "orchestrator")
    workflow.add_edge("salary_agent", "orchestrator")
    workflow.add_edge("tax_agent", "orchestrator")
    workflow.add_edge("cost_of_living_agent", "orchestrator")
    
    async_graph = workflow.compile(checkpointer=memory)
    
    yield
    
    # Cleanup on shutdown
    await db_conn_manager.__aexit__(None, None, None)

app = FastAPI(title="College ROI Agent API", description="API to get college tuition information using an AI agent.", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

from fastapi import Request
import uuid

@app.post("/threads")
async def create_thread():
    """Create a new stateful thread for a LangGraph conversation."""
    thread_id = str(uuid.uuid4())
    return {"id": thread_id, "thread_id": thread_id}

@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, request: Request):
    """
    Execute a step on the LangGraph thread using the provided input messages
    and stream back the LangGraph API-compatible Server-Sent Events.
    React's `useStream` hook expects `messages-tuple` and `values` chunks to be serialized.
    """
    body = await request.json()
    input_data = body.get("input", {})
    
    # We may get raw dict messages or string text, handle them properly
    messages_payload = input_data.get("messages", [])
    
    # LangGraph state expects a dictionary with a 'messages' list containing LangChain BaseMessage objects
    formatted_messages = []
    for m in messages_payload:
        if isinstance(m, dict):
            role = m.get("role")
            content = m.get("content", "")
            if role == "user":
                formatted_messages.append(HumanMessage(content=content))
            elif role == "assistant" or role == "ai":
                formatted_messages.append(AIMessage(content=content))
            elif role == "system":
                formatted_messages.append(SystemMessage(content=content))
            else:
                formatted_messages.append(HumanMessage(content=content))
        else:
            formatted_messages.append(m)
            
    inputs = {"messages": formatted_messages}
    
    stream_modes = body.get("stream_mode", ["messages-tuple", "values"])

    async def generate_chat_stream():
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Iterate over the raw stream chunks and format them into LangGraph SSE protocol
            async for chunk_type, chunk_data in async_graph.astream(inputs, config=config, stream_mode=stream_modes):
                # For messages-tuple, the React Hook expects raw message metadata and the message object
                if chunk_type == "messages-tuple":
                    message_obj, metadata = chunk_data
                    
                    chunk_payload = {
                        "event": "messages-tuple",
                        "data": [
                            {
                                "content": message_obj.content,
                                "id": getattr(message_obj, "id", str(uuid.uuid4())),
                                "type": getattr(message_obj, "type", "ai"),
                                "response_metadata": getattr(message_obj, "response_metadata", {})
                            },
                            metadata
                        ]
                    }
                
                elif chunk_type == "values":
                    data_messages = []
                    if "messages" in chunk_data:
                        for m in chunk_data["messages"]:
                            data_messages.append({
                                "content": m.content,
                                "id": getattr(m, "id", str(uuid.uuid4())),
                                "type": getattr(m, "type", "human" if m.type == "human" else "ai")
                            })
                    
                    state_copy = {}
                    for k, v in chunk_data.items():
                        if k != "messages":
                            state_copy[k] = v
                            
                    chunk_payload = {
                        "event": "values",
                        "data": {
                            **state_copy,
                            "messages": data_messages
                        }
                    }
                else:
                    continue
                    
                # Yield SSE formatted string natively without intermediate JSON parsing where possible
                try:
                    json_str = json.dumps(chunk_payload['data'])
                    yield f"event: {chunk_payload['event']}\\ndata: {json_str}\\n\\n"
                except Exception as e:
                    print(f"Skipping un-serializable chunk: {e}")
                
        except Exception as e:
            print(f"Error in orchestrator stream: {e}")
            error_payload = {"error": str(e)}
            yield f"event: error\\ndata: {json.dumps(error_payload)}\\n\\n"

    return StreamingResponse(generate_chat_stream(), media_type="text/event-stream")

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
