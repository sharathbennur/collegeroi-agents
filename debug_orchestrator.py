from src.orchestrator import get_orchestrator_graph
from langchain_core.messages import HumanMessage
import uuid

def debug():
    # Use a new DB to start fresh
    db_path = "debug_checkpoints.sqlite"
    graph = get_orchestrator_graph(db_path=db_path)
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    print("Sending 'Sharath'...")
    try:
        inputs = {"messages": [HumanMessage(content="Sharath")]}
        # Iterate steps to see where it fails
        for step in graph.stream(inputs, config=config):
            print(f"Step output: {step}")
    except Exception as e:
        print(f"Error on 'Sharath': {e}")
        
    print("\nSending 'What can you do?'...")
    try:
        inputs = {"messages": [HumanMessage(content="What can you do?")]}
        for step in graph.stream(inputs, config=config):
            print(f"Step output: {step}")
    except Exception as e:
        print(f"Error on 'What can you do?': {e}")

if __name__ == "__main__":
    debug()
