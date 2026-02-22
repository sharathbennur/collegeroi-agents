import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from src.tools import web_search, scrape_webpage
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
    
    tools = [web_search, scrape_webpage]
    
    # Create the ReAct agent
    agent = create_react_agent(model, tools)
    
    return agent

TUITION_SYSTEM_PROMPT = """You are a helpful assistant designed to find the per-year tuition cost for a specific college.

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

# Alias for backwards compatibility if still imported anywhere
SYSTEM_PROMPT = TUITION_SYSTEM_PROMPT

SALARY_AGENT_PROMPT = """You are a helpful assistant designed to find the expected post-graduation salary for a given college (and optionally a specific major).

Your process should be:
1. Search for the average starting salary or early-career pay for graduates of the provided college.
2. Scrape the most relevant sources (e.g., PayScale, College Scorecard, university outcome reports).
3. Extract the average/median annual gross salary.
4. Return the FINAL ANSWER as a clear summary of the expected starting annual gross salary.
5. AT THE END of your response, strictly append a section titled "SOURCES:" followed by a list of the URLs you successfully scraped or used to find the information.

If you cannot find the exact number, provide the best estimate based on the data available and explain your reasoning.
"""

TAX_AGENT_PROMPT = """You are a helpful assistant designed to find applicable tax rates for a specific post-graduation location in the US.

Your process should be:
1. Search for the State Income Tax rate for the stated state, and any applicable Local/City Income Tax rates.
2. Provide the effective state and local tax rates (or tax brackets if progressive).
3. Note standard Federal, Medicare, and Social Security implications if necessary, though state and local vary most.
4. Return the FINAL ANSWER summarizing the expected State Income Tax rate and City Income Tax rate for that location.
5. AT THE END of your response, strictly append a section titled "SOURCES:" followed by a list of the URLs you found or used.
"""

COST_OF_LIVING_AGENT_PROMPT = """You are a helpful assistant designed to find reference cost of living ranges for a specific post-graduation city.

Your process should be:
1. Search the web for cost of living indices or rent averages (e.g., Numbeo, RentCafe, etc.) for the target city.
2. Find minimum, median, and high estimates for typical monthly living expenses focusing on: Rent, Groceries, Utilities, Transportation, and Healthcare.
3. Synthesize this data to present reference ranges to the user.
4. Return the FINAL ANSWER as a structured summary showing the Low, Median, and High estimates for each category so the user can be guided to input their own expected lifestyle costs.
5. AT THE END of your response, strictly append a section titled "SOURCES:" followed by a list of the URLs you successfully scraped or used to find the information.
"""
