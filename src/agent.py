import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from src.tools import search_college, scrape_webpage
from dotenv import load_dotenv

load_dotenv()

def get_agent():
    # Initialize the model with OpenRouter
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPEN_ROUTER_API_KEY not found in environment variables")
        
    model = ChatOpenAI(
        model="google/gemini-2.5-flash",
        temperature=0,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    
    tools = [search_college, scrape_webpage]
    
    # Create the ReAct agent
    agent = create_react_agent(model, tools)
    
    return agent

SYSTEM_PROMPT = """You are a helpful assistant designed to find the per-year tuition cost for a specific college.

Your process should be:
1. Search for the college's official tuition page (look for "cost of attendance", "tuition and fees", "room and board", etc.).
2. Scrape the content of the most relevant page.
3. Analyze the text to find the specifics for "Tuition and Fees" and "Room and Board" for an undergraduate student.
4. Report "Tuition and Fees" and "Room and Board" as separate values, and report the sum of the two as the cost-per-year.
5. Differentiate between In-State and Out-of-State if applicable, but prioritize finding the general tuition or out-of-state tuition first.
6. Return the FINAL ANSWER as a clear summary of the estimated cost-per-year.
7. AT THE END of your response, strictly append a section titled "SOURCES:" followed by a list of the URLs you successfully scraped or used to find the information. Each URL should be on a new line.

If you cannot find the exact number, provide the best estimate based on the data available and explain your reasoning.
"""
