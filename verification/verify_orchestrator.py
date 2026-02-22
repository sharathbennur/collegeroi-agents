import sys
from langchain_core.messages import HumanMessage
from src.orchestrator import get_orchestrator_graph, OrchestratorState

def test_orchestrator():
    print("Initializing Orchestrator Graph...")
    graph = get_orchestrator_graph()
    config = {"configurable": {"thread_id": "test_user_2"}}
    
    # Simulate a conversation
    prompts = [
        "Hi, I want to calculate my college ROI.",
        "I want to go to University of Michigan.",
        "I'm going to major in Mechanical Engineering.",
        "I plan to live in Detroit, MI."
    ]
    
    state = OrchestratorState(
        messages=[],
        college_name="", major="", location="",
        tuition_found=False, salary_found=False, taxes_found=False, living_costs_found=False
    )
    
    for user_msg in prompts:
        print(f"\n--- USER: {user_msg} ---")
        state["messages"].append(HumanMessage(content=user_msg))
        
        # We need to parse out the state updates since the orchestrator doesn't natively extract them yet
        # For the sake of the test routing flowing, we'll manually inject the 'found' state if an agent runs
        # and manually extract the entities from the user prompt for the state
        if "Michigan" in user_msg:
            state["college_name"] = "University of Michigan"
        if "Engineering" in user_msg:
            state["major"] = "Mechanical Engineering"
        if "Detroit" in user_msg:
            state["location"] = "Detroit, MI"

        for event in graph.stream(state, config):
            for node_name, node_state in event.items():
                print(f"[{node_name}] -> {node_state['messages'][-1].content[:200]}...")
                
                # Update our test state with any flags the node flipped
                for key in ['tuition_found', 'salary_found', 'taxes_found', 'living_costs_found']:
                    if key in node_state and node_state[key]:
                        state[key] = True
        
        # Update messages history
        latest_msg = list(event.values())[0]["messages"][-1]
        state["messages"].append(latest_msg)
        print(f"\nCURRENT STATE FLAGS: Tuition: {state['tuition_found']}, Salary: {state['salary_found']}, Tax: {state['taxes_found']}, Cost: {state['living_costs_found']}")

if __name__ == "__main__":
    test_orchestrator()
