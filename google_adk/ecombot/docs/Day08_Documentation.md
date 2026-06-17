# Day 8: FastMCP & External Integrations

## Overview
We decouple our order lookup and inventory logic from the ADK tools into an external microservice architecture using the Model Context Protocol (MCP) via `fastmcp`. This mimics a real enterprise architecture where backend systems expose standardized interfaces.

## Learning Objectives
- Understanding the Model Context Protocol (MCP).
- Creating lightweight python FastMCP servers.
- Connecting an ADK agent to an external MCP JSON-RPC service.
- Robust error handling for remote tool execution.

## Architecture
- **eComBot (ADK)**: Uses wrapper tools (e.g. `mcp_get_order_status`).
- **MCP Client**: Initiates HTTP POST JSON-RPC calls over to the MCP server.
- **FastMCP Orders Server**: Runs on port 8001. Handles order lookups and cancellations.
- **FastMCP Inventory Server**: Runs on port 8002. Handles stock checks and variant lookups.

## Files Created/Modified

### `orders_server.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/services/mcp_servers/orders_server.py`
- **Purpose**: Defines an MCP server with `get_order_status` tools.
- **Key Components**: Uses `@mcp.tool()` decorators.

### `mcp_order_tools.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/tools/mcp_order_tools.py`
- **Purpose**: ADK `@tool` stubs that proxy requests to the MCP servers.
- **Key Components**: Uses `httpx.AsyncClient` with proper timeout catching.

### `support_agent.py`
- **Path**: `c:/Users/gokku/.gemini/antigravity/scratch/capstone/google_adk/ecombot/src/agents/support_agent.py`
- **Purpose**: Determines which tool array to load based on `MCP_ENABLED`.
- **Key Components**: Swaps local DB tools for MCP proxy tools.

## How to Run / Test

### Starting the Services
You will need three separate terminal windows:
1. **Terminal 1**: Start the FastMCP Orders Server:
   ```bash
   python src/services/mcp_servers/orders_server.py
   ```
2. **Terminal 2**: Start the FastMCP Inventory Server:
   ```bash
   python src/services/mcp_servers/inventory_server.py
   ```
3. **Terminal 3**: Ensure `.env` has `MCP_ENABLED=True`, then start the agent:
   ```bash
   python src/agents/support_agent.py
   ```

### Verification Test Cases

**Test Case 1: Basic MCP Tool Invocation**
- **User Input**: "Do you have the Mechanical Keyboard in stock?"
- **Expected Outcome**: The agent calls the proxy tool `mcp_check_stock`. The HTTP call hits the FastMCP inventory server on port 8002, reporting back that it's out of stock.

**Test Case 2: Error Handling & Resilience**
- **User Input**: "Can you check order ORD-999?"
- **Expected Outcome**: The tool triggers a simulated timeout delay on the backend (configured in `mock_data.py`). The `mcp_order_tools` wrapper catches the `httpx.TimeoutException`, returns a graceful fallback error dictionary, and the agent responds to the user apologizing for the technical delay rather than crashing.

## Key Concepts Covered
- Microservice tool exposure with MCP.
- Client-Server tool separation.
- Managing asynchronous tool failures and timeouts gracefully.
