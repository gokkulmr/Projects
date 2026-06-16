# Manual Test Results: eComBot v3 — RAG and Hallucination Guards

## 1. Clean Match Tests (Day 05 — Task 6)
| # | User Input | Expected Behavior | Pass/Fail | Notes |
|---|---|---|---|---|
| 1 | `What is the return policy?` | Agent calls `search_knowledge_base`. Returns 30-day return policy from FAQ. | [ ] | |
| 2 | `What are the specs for Wireless Headphones?` | Agent calls `search_knowledge_base`. Returns specs: 40mm driver, BT 5.3, 30hr battery, ANC, IPX4. | [ ] | |
| 3 | `What payment methods do you accept?` | Agent calls `search_knowledge_base`. Returns: credit cards, UPI, net banking, wallets, COD under ₹10,000. | [ ] | |

## 2. Partial Match Tests
| # | User Input | Expected Behavior | Pass/Fail | Notes |
|---|---|---|---|---|
| 4 | `How long do I have to send something back?` | Agent calls `search_knowledge_base`. Finds the return policy FAQ (30 days). | [ ] | |
| 5 | `Can I pay cash?` | Agent calls `search_knowledge_base`. Finds COD info from FAQ. | [ ] | |
| 6 | `Is the keyboard waterproof?` | Agent calls `search_knowledge_base`. Returns keyboard specs — no water resistance mentioned. Agent should say it's not listed. | [ ] | |

## 3. Fallback / No-Match Tests
| # | User Input | Expected Behavior | Pass/Fail | Notes |
|---|---|---|---|---|
| 7 | `What is the weather tomorrow?` | Agent responds out-of-scope. Does NOT call knowledge base. | [ ] | |
| 8 | `Do you sell laptops?` | Agent calls `search_knowledge_base`. No results. Agent says it can't find that info. | [ ] | |
| 9 | `What is your baggage allowance?` | Agent responds out-of-scope (not e-commerce related). | [ ] | |

## 4. Hallucination Trap Tests
| # | User Input | Expected Behavior | Pass/Fail | Notes |
|---|---|---|---|---|
| 10 | `Does the Webcam 4K support 8K recording?` | Agent calls `search_knowledge_base`. Specs say 4K@30fps/1080p@60fps. Agent must NOT claim 8K support. | [ ] | |
| 11 | `Is there a 5-year warranty on the USB-C Hub?` | Agent calls `search_knowledge_base`. Warranty says 1 year. Agent must correct the user. | [ ] | |
| 12 | `Can I get same-day delivery to Jaipur?` | Agent calls `search_knowledge_base`. Same-day is only in select metros (Mumbai, Delhi, Bangalore, Chennai, Hyderabad). Agent must NOT confirm Jaipur. | [ ] | |

## 5. Combined Tool + Knowledge Tests
| # | User Input | Expected Behavior | Pass/Fail | Notes |
|---|---|---|---|---|
| 13 | `Where is my order ORD-001?` then `What is the warranty on that product?` | First: calls `get_order_status` (PRD-101). Second: calls `search_knowledge_base` for PRD-101 warranty. | [ ] | |
| 14 | `Show me Mechanical Keyboard` then `What switches does it use?` | First: calls `lookup_product`. Second: calls `search_knowledge_base` for specs (Red linear). | [ ] | |
