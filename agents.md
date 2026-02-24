# Agents

This project implements AI agents using LangChain and LangGraph to research and calculate college tuition costs.

## Core Agent: Tuition Researcher

The core agent is a ReAct agent powered by `google/gemini-2.5-flash` via OpenRouter.

### Capabilities
- **Search**: Uses DuckDuckGo to find relevant college tuition pages.
- **Scrape**: Scrapes the content of tuition pages to extract specific cost data.
- **Synthesize**: combines gathered data to report tuition, room & board, and total cost of attendance.

### Implementation
- **Source**: `src/agent.py`
- **Agents**: Tuition, Salary, Tax, and Cost of Living agents.
- **Tools**: `src/tools.py` (`web_search`, `scrape_webpage`)

## Interfaces

The agent is exposed through multiple interfaces:

### 1. Command Line Interface (CLI)
- **File**: `main.py`
- **Usage**: `python main.py "College Name"`
- **Function**: Runs a single research task to find the 4-year tuition cost.

### 2. FastAPI Backend
- **File**: `server.py`
- **Endpoints**:
    - `GET /college/{college_name}`: Returns tuition info and sources.
    - `POST /personalized-cost`: Returns a personalized breakdown based on aid.
    - `POST /chat`: Stateful session chat using the Orchestrator. Returns a Server-Sent Events (SSE) stream compatible with React `useStream` hooks.
- **Function**: REST API wrapper around the agent.

### 3. MCP Server (Model Context Protocol)
- **File**: `mcp_server.py`
- **Tools**:
    - `get_college_tuition(college_name)`: Finds general tuition information.
    - `get_personalized_cost(college_name, family_contribution, financial_aid)`: Calculates net price and remaining gap based on user's financial situation.
- **Function**: Exposes agent capabilities as tools for MCP clients (e.g., Claude Desktop, other AI assistants).

## Orchestrator Agent (State & Memory)

The Orchestrator manages the user's session, keeping track of history and specific stateful information.

### Capabilities
- **Memory**: Uses `SqliteSaver` to persist conversation state and user progress.
- **State Tracking**: Maintains a list of colleges researched and user-validated information.
- **Routing**: Delegates research tasks to the core Research Agent.

### Implementation
- **Source**: `src/orchestrator.py`
- **Persistence**: SQLite (checkpoints.sqlite)
