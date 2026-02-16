# College ROI Agents

A suite of AI agents designed to research and report college tuition costs and financial return on investment.

## Features

- **Tuition Research**: Automatically finds current tuition, room, and board costs for any US college.
- **Personalized Estimates**: Calculates net price and remaining gaps based on family contribution and expected aid.
- **User Session Memory**: Persistence for user queries and validated information using LangGraph Orchestration.
- **Multi-Interface**:
  - **CLI**: Simple command-line tool for quick queries.
  - **REST API**: FastAPI backend for integration into web apps.
  - **MCP Server**: Model Context Protocol support for use with AI assistants like Claude Desktop.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/sharathbennur/collegeroi-agents.git
    cd collegeroi-agents
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` is missing, you'll need `langchain`, `langgraph`, `fastapi`, `uvicorn`, `mcp`, `beautifulsoup4`, `requests`, `python-dotenv`, etc.)*

3.  **Environment Configuration**:
    Create a `.env` file in the root directory:
    ```bash
    OPEN_ROUTER_API_KEY=your_api_key_here
    ```

## Usage

### Command Line Interface (CLI)
### Command Line Interface (CLI)
Interact with the Orchestrator Agent in a stateful chat:
```bash
python main.py
```
Or start with an initial query:
```bash
python main.py "Stanford University"
```
The session maintains memory of previous questions.

### FastAPI Server
Start the REST API server:
```bash
python server.py
```
The API will be available at `http://localhost:8000`.
- Docs: `http://localhost:8000/docs`
- Query: `GET /college/{college_name}`
- Personalized: `POST /personalized-cost` (Body: `{"college_name": "string", "family_contribution": int, "financial_aid": int}`)
- Chat: `POST /chat` (Body: `{"message": "string", "user_id": "string"}`)

### MCP Server
Run the MCP server (typically used by an MCP client):
```bash
python mcp_server.py
```
This exposes the `get_college_tuition` and `get_personalized_cost` tools.

## Development

### Verification
Run the verification suite to ensure all components are working:
```bash
python verification/run_all.py
```
This runs tests for:
- Tools (`verify_tools.py`)
- Personalized Cost Agent (`verify_personalized_cost.py`)
- Orchestrator/State Memory (`verify_orchestrator.py`)
- CLI Logic (`verify_cli.py`)

## License

[MIT](LICENSE)
