# Manual Testing Guide — FastMCP Integration (Day 8)

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure ports **8001** and **8002** are free on localhost.

---

## 1. Start the MCP Servers

Open **two separate terminals** (both from the `src/` directory):

### Terminal 1 — Orders Server (port 8001)
```bash
cd src
python -m services.mcp_servers.orders_server
```
Expected output:
```
Starting FastMCP server "ecombot-orders" on 127.0.0.1:8001
```

### Terminal 2 — Inventory Server (port 8002)
```bash
cd src
python -m services.mcp_servers.inventory_server
```
Expected output:
```
Starting FastMCP server "ecombot-inventory" on 127.0.0.1:8002
```

---

## 2. Test Cases — Orders Server

Use `curl`, `httpie`, or any HTTP client to send JSON-RPC requests to `http://127.0.0.1:8001/mcp`.

### 2.1 Get Order Status (valid order)
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "get_order_status", "arguments": {"order_id": "ORD-001"}}
  }'
```
**Expected**: `"ok": true`, status = `"shipped"`, customer = `"Priya Sharma"`.

### 2.2 Get Order Details (full details)
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "get_order_details", "arguments": {"order_id": "ORD-001"}}
  }'
```
**Expected**: `"ok": true`, includes `shipping_carrier`, `tracking_number`, `estimated_delivery`.

### 2.3 Cancel Order — Processing (should succeed)
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "cancel_order", "arguments": {"order_id": "ORD-004", "reason": "Changed mind"}}
  }'
```
**Expected**: `"ok": true`, message confirming cancellation.

### 2.4 Cancel Order — Already Shipped (should fail)
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "cancel_order", "arguments": {"order_id": "ORD-001"}}
  }'
```
**Expected**: `"ok": false`, error mentions "already shipped".

### 2.5 Invalid Order ID
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "get_order_status", "arguments": {"order_id": "INVALID"}}
  }'
```
**Expected**: `"ok": false`, error mentions "Invalid order ID format".

### 2.6 Order Not Found
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "get_order_status", "arguments": {"order_id": "ORD-777"}}
  }'
```
**Expected**: `"ok": false`, error mentions "not found".

### 2.7 Timeout Simulation
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  --max-time 5 \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "get_order_status", "arguments": {"order_id": "ORD-999"}}
  }'
```
**Expected**: Request hangs until client timeout. Server sleeps 30 s internally.

### 2.8 Internal Error Simulation
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "get_order_status", "arguments": {"order_id": "ORD-888"}}
  }'
```
**Expected**: `"ok": false`, error mentions "Internal server error".

---

## 3. Test Cases — Inventory Server

Send requests to `http://127.0.0.1:8002/mcp`.

### 3.1 Check Stock — In Stock
```bash
curl -X POST http://127.0.0.1:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "check_stock", "arguments": {"product_id": "PRD-101"}}
  }'
```
**Expected**: `"ok": true`, `available = 47`, `in_stock = true`.

### 3.2 Check Stock — Out of Stock
```bash
curl -X POST http://127.0.0.1:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "check_stock", "arguments": {"product_id": "PRD-102"}}
  }'
```
**Expected**: `"ok": true`, `available = 0`, `in_stock = false`, includes `restock_date`.

### 3.3 Check Stock — Discontinued
```bash
curl -X POST http://127.0.0.1:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "check_stock", "arguments": {"product_id": "PRD-105"}}
  }'
```
**Expected**: `"ok": false`, error mentions "discontinued".

### 3.4 List Variants — Colors
```bash
curl -X POST http://127.0.0.1:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "list_variants", "arguments": {"product_id": "PRD-101"}}
  }'
```
**Expected**: 3 variants with `color` field: Black, White, Navy Blue.

### 3.5 List Variants — Switches
```bash
curl -X POST http://127.0.0.1:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "list_variants", "arguments": {"product_id": "PRD-102"}}
  }'
```
**Expected**: 3 variants with `switch` field: Red, Blue, Brown.

### 3.6 Invalid Product ID
```bash
curl -X POST http://127.0.0.1:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "check_stock", "arguments": {"product_id": "INVALID"}}
  }'
```
**Expected**: `"ok": false`, error mentions "Invalid product ID format".

### 3.7 Product Not Found
```bash
curl -X POST http://127.0.0.1:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "check_stock", "arguments": {"product_id": "PRD-999"}}
  }'
```
**Expected**: `"ok": false`, error mentions "not found".

---

## 4. Running Automated Tests

```bash
cd <project_root>
python -m pytest tests/test_mcp_integration.py -v
```

All tests should pass without any running servers (they call the tool functions directly).

---

## 5. Cleanup

Press **Ctrl+C** in each terminal to stop the MCP servers.
