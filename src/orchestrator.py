import os
import sqlite3
from typing import Annotated, List, TypedDict, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.agent import get_agent, SYSTEM_PROMPT as RESEARCH_PROMPT
from dotenv import load_dotenv

load_dotenv()

# Define the state schema
class OrchestratorState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation history"]
    colleges_queried: List[str]
    validated_info: Dict[str, str]  # college_name -> status (e.g., "confirmed", "incorrect")

def get_model():
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    return ChatOpenAI(
        model="google/gemini-2.5-flash",
        temperature=0,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

def orchestrator_node(state: OrchestratorState):
    """
    The orchestrator decides what to do based on user input.
    It can call the research agent, update validation status, or just chat.
    """
    model = get_model()
    
    # System prompt for the orchestrator
    system_msg = SystemMessage(content=f"""You are the College ROI Orchestrator. 
    Your job is to manage the user's research journey.
    
    CURRENT STATE:
    - Colleges Queried: {state.get('colleges_queried', [])}
    - Validated Info: {state.get('validated_info', {})}
    
    GUIDELINES:
    1. If the user asks for tuition info for a college, you should acknowledge it and initiate research.
    2. If the user confirms that the info you found is correct, update the 'validated_info'.
    3. Keep track of which colleges have been visited.
    
    Respond to the user naturally. If you need to perform research, explicitly state that you are calling the research agent.
    """)
    
    messages = [system_msg] + state["messages"]
    response = model.invoke(messages)
    
    # Simple heuristic to update state (in a complex app, we'd use structured output)
    new_colleges = list(state.get("colleges_queried", []))
    # Basic logic: if a college name is mentioned in a query for the first time, add it
    # For now, we'll keep it simple and just return the AI response.
    
    return {"messages": [response]}

def research_node(state: OrchestratorState):
    """
    Calls the underlying research agent.
    """
    agent = get_agent()
    # Pass the last user message to the research agent
    last_user_message = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")
    
    result = agent.invoke({"messages": [HumanMessage(content=last_user_message)]})
    agent_response = result["messages"][-1]
    
    # Update queried colleges list if we found info
    new_colleges = list(state.get("colleges_queried", []))
    # Dummy logic to extract college - ideally use the model
    # For this demo, we'll just append a placeholder or assume extraction happened
    
    return {
        "messages": [agent_response],
        # We'd update colleges_queried here if we had a clean extraction
    }

def get_orchestrator_graph(db_path="checkpoints.sqlite"):
    # Initialize the checkpoint saver
    # Note: SqliteSaver requires a connection
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    workflow = StateGraph(OrchestratorState)
    
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("researcher", research_node)
    
    # Define the flow
    workflow.add_edge(START, "orchestrator")
    
    # Simplified routing: if user asks for research, go to researcher, then back to orchestrator
    # For now, let's just make it a simple linear flow for demonstration or 
    # use conditional edges if we want to be fancy.
    
    def route_orchestrator(state: OrchestratorState):
        last_ai_msg = state["messages"][-1].content.lower()
        if "calling the research agent" in last_ai_msg or "researching" in last_ai_msg:
            return "researcher"
        return END

    workflow.add_conditional_edges("orchestrator", route_orchestrator)
    workflow.add_edge("researcher", END) # Or back to orchestrator
    
    return workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    # Quick test
    graph = get_orchestrator_graph()
    config = {"configurable": {"thread_id": "user_1"}}
    
    input_msg = OrchestratorState(
        messages=[HumanMessage(content="Find tuition for Stanford")],
        colleges_queried=[],
        validated_info={}
    )
    
    for event in graph.stream(input_msg, config):
        for value in event.values():
            print(f"Assistant: {value['messages'][-1].content}")
