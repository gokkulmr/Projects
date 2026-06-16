# Manual Test Results: eComBot v2

## 1. Core Flow Validation (Task 9)
| Turn | User Input | Expected Behavior | Pass/Fail | Notes |
|---|---|---|---|---|
| 1 | `Hi, my name is Priya.` | Agent greets Priya. Name is stored in Redis session state. | [ ] | |
| 2 | `Where is my order ORD-001?` | Agent triggers `get_order_status` tool via PostgreSQL. Returns structured order details. | [ ] | |
| 3 | `What about that same order?` | Agent reuses `ORD-001` from session state. No need to ask for ID again. | [ ] | |
| 4 | `Show me PRD-101` | Agent triggers `lookup_product` tool via PostgreSQL. Returns product details. | [ ] | |
| 5 | `What is the price again?` | Agent reuses `PRD-101` from session state. | [ ] | |
| 6 | **[RESTART APP]** `Is my order still delayed?` | Agent remembers `ORD-001` because Redis restored the session state. | [ ] | |

## 2. Failure Handling Validation (Task 10)
| Scenario | User Input | Expected Behavior | Pass/Fail | Notes |
|---|---|---|---|---|
| Invalid Order ID | `Check order ORD-999` | Tool returns a clean "Order not found" message. Agent relays politely. | [ ] | |
| Missing Input | `Cancel my order` | Agent asks "Which order ID would you like to cancel?" instead of guessing. | [ ] | |
| DB Disconnect | `Check PRD-101` (while Postgres container is paused) | Tool catches exception and returns "Our system is temporarily unavailable." No stack traces leaked. | [ ] | |