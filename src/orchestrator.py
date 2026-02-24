import os
import sqlite3
from typing import Annotated, List, TypedDict, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.agent import (
    get_agent, 
    SYSTEM_PROMPT as TUITION_PROMPT,
    SALARY_AGENT_PROMPT,
    TAX_AGENT_PROMPT,
    COST_OF_LIVING_AGENT_PROMPT
)
from dotenv import load_dotenv

load_dotenv()

# Define the state schema
class OrchestratorState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    
    # State flags to track calculation progress
    college_name: str
    major: str
    location: str
    
    tuition_found: bool
    salary_found: bool
    taxes_found: bool
    living_costs_found: bool

def get_model():
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    return ChatOpenAI(
        model="google/gemini-2.5-flash",
        temperature=0,
        streaming=True,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

def orchestrator_node(state: OrchestratorState):
    """
    The orchestrator manages the step-by-step data collection journey.
    """
    model = get_model()
    
    # Extract current state for prompting
    college = state.get('college_name', 'Not provided')
    major = state.get('major', 'Not provided')
    location = state.get('location', 'Not provided')
    
    system_msg = SystemMessage(content=f"""You are the College ROI Orchestrator. 
    Your goal is to collect all necessary data for an expected ROI calculation.
    
    CURRENT STATE:
    - Target College: {college} (Tuition Found: {state.get('tuition_found', False)})
    - Planned Major: {major} (Salary Found: {state.get('salary_found', False)})
    - Planned Post-Grad Location: {location} 
        (Taxes Found: {state.get('taxes_found', False)})
        (Living Costs Found: {state.get('living_costs_found', False)})
    
    Your job is to progress the research SEQUENTIALLY. Guide the user if they haven't provided info.
    1. If College is unknown -> Ask for the College.
    2. If College is known but Tuition is False -> Route to TUITION agent.
    3. If Tuition is True but Major is unknown -> Ask the user for their planned major (or if they are undecided).
    4. If Major is known (or undecided) but Salary is False -> Route to SALARY agent.
    5. If Salary is True but Location is unknown -> Ask where they plan to live and work after graduation (City, State).
    6. If Location is known but Taxes are False -> Route to TAX agent.
    7. If Taxes are True but Living Costs are False -> Route to LIVING_COSTS agent.
    8. Once all flags are True, summarize that data collection is complete and the ROI calculator can be executed.
    
    HOW TO ROUTE:
    If you need to call an agent to fetch data based on the sequential rules above, output EXACTLY ONE of the following routing tags at the very end of your message:
    [ROUTE: TUITION]
    [ROUTE: SALARY]
    [ROUTE: TAX]
    [ROUTE: COST_OF_LIVING]
    
    Otherwise, just converse with the user normally to ask for the missing information.
    """)
    
    messages = [system_msg] + state["messages"]
    response = model.invoke(messages)
    
    return {"messages": [response]}

# Helper to run an agent and update state flags
def create_agent_node(prompt: str, flag_to_update: str):
    def agent_node(state: OrchestratorState):
        agent = get_agent()
        # Find the last actual user request or the orchestrator's synthesized instruction
        last_message = next((m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), "")
        
        # Add context from state so the agent knows what to search for
        college = state.get('college_name', '')
        major = state.get('major', '')
        location = state.get('location', '')
        
        context_prompt = f"{prompt}\n\nCURRENT TARGETS for this search:\n- College: {college}\n- Major: {major}\n- Location: {location}"
        
        # Inject the contextual prompt
        inputs = {"messages": [SystemMessage(content=context_prompt), HumanMessage(content=last_message)]}
        result = agent.invoke(inputs)
        
        return {
            "messages": [result["messages"][-1]],
            flag_to_update: True
        }
    return agent_node

# Define specific nodes
tuition_node = create_agent_node(TUITION_PROMPT, "tuition_found")
salary_node = create_agent_node(SALARY_AGENT_PROMPT, "salary_found")
tax_node = create_agent_node(TAX_AGENT_PROMPT, "taxes_found")
cost_of_living_node = create_agent_node(COST_OF_LIVING_AGENT_PROMPT, "living_costs_found")

def get_orchestrator_graph(db_path="checkpoints.sqlite"):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    workflow = StateGraph(OrchestratorState)
    
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tuition_agent", tuition_node)
    workflow.add_node("salary_agent", salary_node)
    workflow.add_node("tax_agent", tax_node)
    workflow.add_node("cost_of_living_agent", cost_of_living_node)
    
    # Define the flow
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
    
    # All agents route back to orchestrator to determine the next step
    workflow.add_edge("tuition_agent", "orchestrator")
    workflow.add_edge("salary_agent", "orchestrator")
    workflow.add_edge("tax_agent", "orchestrator")
    workflow.add_edge("cost_of_living_agent", "orchestrator")
    
    return workflow.compile(checkpointer=memory)

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_orchestrator_graph(db_path="checkpoints.sqlite"):
    """
    Async version of the graph for streaming API endpoints.
    Yields the compiled graph with an AsyncSqliteSaver connected to the DB.
    """
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    
    # Needs to be an async context manager to handle the DB connection cleanly
    async with AsyncSqliteSaver.from_conn_string(db_path) as memory:
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
        
        yield workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    # Test script in verification
    pass
