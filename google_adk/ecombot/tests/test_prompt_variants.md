# Prompt Variant Testing Guide

## Overview
This document defines test scenarios for evaluating different prompt variants used across the eComBot agent system.

## Prompt Variants

### Variant 1: Support Agent (`support_instructions_v1.txt`)
- **Style**: Comprehensive, detailed tool documentation
- **Scope**: Full support coverage including product lookup
- **Hallucination guards**: Explicit rules with examples

### Variant 2: Support Agent (`support_instructions_v2.txt`)
- **Style**: Concise, focused on support-only scope
- **Scope**: Excludes product recommendations (delegates to Sales)
- **Hallucination guards**: Simplified but strict

### Variant 3: Sales Agent (`sales_instructions_v2.txt`)
- **Style**: Sales-focused, recommendation-oriented
- **Scope**: Product discovery, comparisons, buying advice
- **Hallucination guards**: Tool-based answers only

## Test Scenarios

### Test 1: Greeting Response
| Query | V1 Expected | V2 Expected |
|-------|-------------|-------------|
| "Hi!" | Professional greeting, mentions capabilities | Professional greeting |
| "What can you do?" | Lists all capabilities | Lists support-only capabilities |

### Test 2: Order Lookup
| Query | V1 Expected | V2 Expected |
|-------|-------------|-------------|
| "Where is ORD-001?" | Calls get_order_status, shows details | Same |
| "Track my order" | Asks for order ID | Same |

### Test 3: Product Questions
| Query | V1 Expected | V2 Expected |
|-------|-------------|-------------|
| "Show me Wireless Headphones" | Calls lookup_product | Delegates to Sales Agent |
| "Compare keyboards" | Calls search_knowledge_base | Delegates to Sales Agent |

### Test 4: Policy Questions
| Query | V1 Expected | V2 Expected |
|-------|-------------|-------------|
| "What is your return policy?" | Calls search_knowledge_base | Same |
| "Warranty on headphones?" | Calls search_knowledge_base | Same |

### Test 5: Out-of-Scope
| Query | V1 Expected | V2 Expected |
|-------|-------------|-------------|
| "Write me Python code" | Polite refusal | Same |
| "What's the weather?" | Polite refusal | Same |

### Test 6: Hallucination Traps
| Query | V1 Expected | V2 Expected |
|-------|-------------|-------------|
| "Is the iPhone 15 available?" | Searches, reports not found | Same |
| "What's the warranty on Samsung TV?" | Searches, reports not in knowledge base | Same |

### Test 7: Session Context
| Turn | Query | Expected |
|------|-------|----------|
| 1 | "My name is Priya" | Acknowledges name |
| 2 | "Check ORD-001" | Calls tool, shows order |
| 3 | "What about that order?" | Reuses ORD-001 from session |
| 4 | "Can I cancel it?" | Attempts cancel on ORD-001 |

## How to Run

### Against v1 (single agent):
```bash
python -m src.agents.support_agent
```

### Against v2 (orchestrated):
```bash
python -m src.agents.orchestrator
```

### Against Chainlit UI:
```bash
chainlit run src/ui/chainlit_app.py -w
```

Manually run each test scenario and compare behavior between variants.
