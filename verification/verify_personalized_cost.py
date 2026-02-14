import asyncio
import os
from mcp_server import get_personalized_cost

# Mock the mcp object to avoid issues if the decorator interferes, 
# but usually we can just call the decorated function if it's a simple wrapper.
# If it fails, we will know.

async def main():
    print("Starting verification of get_personalized_cost...")
    
    # Test data
    college = "Standford University" # Typo intended to see if search handles it, or use "Stanford University"
    college = "Stanford University"
    contribution = 15000
    aid = 40000
    
    print(f"College: {college}")
    print(f"Family Contribution: ${contribution}")
    print(f"Financial Aid: ${aid}")
    
    try:
        result = await get_personalized_cost(college, contribution, aid)
        print("\n--- Result ---\n")
        print(result)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
