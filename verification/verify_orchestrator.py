import asyncio
import os
import sqlite3
from src.orchestrator import get_orchestrator_graph
from langchain_core.messages import HumanMessage
from termcolor import colored

async def test_orchestrator_memory():
    print(colored("Starting verification of Orchestrator Agent & State Management...", "cyan"))
    
    db_path = "test_checkpoints.sqlite"
    # Remove existing test db if any
    if os.path.exists(db_path):
        os.remove(db_path)
        
    graph = get_orchestrator_graph(db_path=db_path)
    user_id = "test_user_123"
    config = {"configurable": {"thread_id": user_id}}
    
    # Step 1: Initial query
    print(colored(f"\n[Step 1] Asking about Stanford...", "yellow"))
    input_1 = {"messages": [HumanMessage(content="Hi, I want to research tuition for Stanford University.")]}
    
    # We use loop.run_in_executor because our graph.invoke is synchronous (wraps sync agent)
    loop = asyncio.get_event_loop()
    
    def run_1():
        return graph.invoke(input_1, config=config)
    
    result_1 = await loop.run_in_executor(None, run_1)
    print(f"Assistant: {result_1['messages'][-1].content[:200]}...")
    
    # Step 2: Follow-up query to check memory
    print(colored(f"\n[Step 2] Asking a follow-up about 'it' (memory check)...", "yellow"))
    input_2 = {"messages": [HumanMessage(content="Wait, actually tell me about Harvard instead.")]}
    
    def run_2():
        return graph.invoke(input_2, config=config)
        
    result_2 = await loop.run_in_executor(None, run_2)
    print(f"Assistant: {result_2['messages'][-1].content[:200]}...")
    
    # Step 3: Check SQLite to see if checkpoints exist
    print(colored(f"\n[Step 3] Verifying SQLite persistence...", "yellow"))
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM checkpoints")
        count = cursor.fetchone()[0]
        conn.close()
        print(colored(f"Success: Found {count} checkpoints in {db_path}", "green"))
    else:
        print(colored(f"Failure: {db_path} was not created!", "red"))

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
        print(colored("Cleaned up test database.", "cyan"))

if __name__ == "__main__":
    asyncio.run(test_orchestrator_memory())
