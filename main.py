import argparse
import sys
from src.agent import get_agent, SYSTEM_PROMPT
from langchain_core.messages import SystemMessage

def main():
    parser = argparse.ArgumentParser(description="Find 4-year tuition costs for a college.")
    parser.add_argument("college_name", type=str, help="Name of the college")
    args = parser.parse_args()
    
    try:
        agent = get_agent()
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print("Make sure you have set OPENAI_API_KEY in your environment or .env file.")
        sys.exit(1)
    
    print(f"Researching tuition for: {args.college_name}...")
    print("This may take a minute as the agent searches and verifies information...\n")
    
    inputs = {"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        ("user", f"Find the per-year tuition cost for {args.college_name}")
    ]}
    
    try:
        result = agent.invoke(inputs)
        # The last message is the result from the assistant
        print("\n--- Result ---\n")
        print(result["messages"][-1].content)
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")

if __name__ == "__main__":
    main()
