---
description: Steps to follow when adding new agents or features
---

When adding new agents or creating new features in the `collegeroi-agents` repository, follow these steps:

1.  **Update `README.md`**: Ensure the top-level documentation reflects the new feature or agent.
2.  **Update `agents.md`**: Add or update the description of the agent, its capabilities, and its interfaces in `agents.md`.
3.  **Handle New Agents**:
    *   **Ask for API endpoint**: If it's a new agent, ask the user if a corresponding API endpoint (e.g., in `server.py`) is needed.
    *   **Add to MCP Server**: Automatically add the new agent or its capabilities as a tool in `mcp_server.py`.
4.  **Verify MCP Server**: Ensure the `mcp_server.py` correctly imports and exposes the new functionality.
