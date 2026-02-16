import argparse
import sys
import uuid
from src.orchestrator import get_orchestrator_graph
from langchain_core.messages import HumanMessage

def main():
    parser = argparse.ArgumentParser(description="Chat with the College ROI Orchestrator.")
    parser.add_argument("college_name", type=str, nargs="?", help="Name of the college (optional initial query)")
    args = parser.parse_args()
    
    # Initialize the graph
    try:
        # Use a persistent simple checkpoint file for the CLI session
        # In a real app we might want configurable paths or user IDs
        graph = get_orchestrator_graph(db_path="cli_checkpoints.sqlite")
    except Exception as e:
        print(f"Error initializing orchestrator: {e}")
        print("Make sure you have set OPEN_ROUTER_API_KEY in your environment or .env file.")
        sys.exit(1)
        
    # Generate a session ID for this run
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("Welcome to the College ROI Agent CLI!")
    print("Type 'quit', 'exit', or Ctrl+C to stop.\n")
    
    # Handle initial argument if provided
    initial_input = None
    if args.college_name:
        initial_input = f"Find the per-year tuition cost for {args.college_name}"
        print(f"You: {initial_input}")
    
    while True:
        try:
            user_input = initial_input if initial_input else input("You: ")
            initial_input = None # Clear after first use
            
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue
                
            print("Assistant: (Thinking...)", end="\r")
            
            inputs = {"messages": [HumanMessage(content=user_input)]}
            result = graph.invoke(inputs, config=config)
            
            # Print the final response
            print(f"Assistant: {result['messages'][-1].content}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    main()
