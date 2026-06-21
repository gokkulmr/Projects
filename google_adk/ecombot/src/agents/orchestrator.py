"""eComBot v6 — Multi-Agent Orchestrator.

Routes user queries to Support or Sales specialist agents.
"""

import asyncio
import os
import re
import sys
import logging

# project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.genai import types

from config.settings import (
    LLM_MODEL,
    LLM_BASE_URL,
    OPENROUTER_API_KEY,
    LITELLM_PROXY_ENABLED,
    MCP_ENABLED,
)

from agents.tracing import OrchestrationTracer

# Force the API key into the environment for LiteLLM
os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

# Logging cleanup
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not set")
    sys.exit(1)

# -------------------------------------------------------
# Load instruction files
# -------------------------------------------------------
def _load_instructions(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

ORCHESTRATOR_INSTRUCTIONS = _load_instructions("orchestrator_instructions.txt")
SUPPORT_INSTRUCTIONS = _load_instructions("support_instructions_v2.txt")
SALES_INSTRUCTIONS = _load_instructions("sales_instructions_v2.txt")

# -------------------------------------------------------
# LLM model
# -------------------------------------------------------
if LITELLM_PROXY_ENABLED:
    from gateway.proxy_client import GatewayClient
    _gw = GatewayClient()
    llm_model = _gw.create_gateway_model()
else:
    llm_model = LiteLlm(
        model=LLM_MODEL,
        api_key=OPENROUTER_API_KEY,
        api_base=LLM_BASE_URL,
    )

# -------------------------------------------------------
# Tools
# -------------------------------------------------------
from tools.order_tools import get_order_status, cancel_order
from tools.product_tools import lookup_product
from tools.knowledge_tools import search_knowledge_base

if MCP_ENABLED:
    from tools.mcp_order_tools import (
        mcp_get_order_status,
        mcp_cancel_order,
        mcp_check_stock,
        mcp_list_variants,
    )
    support_tools = [mcp_get_order_status, mcp_cancel_order, mcp_check_stock, mcp_list_variants, search_knowledge_base]
else:
    support_tools = [get_order_status, cancel_order, search_knowledge_base]

sales_tools = [lookup_product, search_knowledge_base]

# -------------------------------------------------------
# Sub-agents
# -------------------------------------------------------
support_agent = LlmAgent(
    name="support_agent",
    model=llm_model,
    instruction=SUPPORT_INSTRUCTIONS,
    tools=support_tools,
    description="Handles order tracking, cancellations, returns, refunds, shipping issues, and support FAQ.",
)

sales_agent = LlmAgent(
    name="sales_agent",
    model=llm_model,
    instruction=SALES_INSTRUCTIONS,
    tools=sales_tools,
    description="Handles product recommendations, comparisons, specs, pricing, and buying advice.",
)

# -------------------------------------------------------
# Orchestrator (root agent with sub_agents)
# -------------------------------------------------------
orchestrator = LlmAgent(
    name="ecombot_orchestrator",
    model=llm_model,
    instruction=ORCHESTRATOR_INSTRUCTIONS,
    sub_agents=[support_agent, sales_agent],
    description="Central coordinator that routes queries to Support or Sales agents.",
)

# -------------------------------------------------------
# Session + Runner
# -------------------------------------------------------
from services.session_service import create_session_service

session_service = create_session_service()
APP_NAME = "ecombot-v6-orchestrator"
USER_ID = "user-1"
SESSION_ID = "session-1"

runner = Runner(
    agent=orchestrator,
    app_name=APP_NAME,
    session_service=session_service,
)

# Tracer
tracer = OrchestrationTracer()

# -------------------------------------------------------
# Intent classifier (pattern-based)
# -------------------------------------------------------
_SUPPORT_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\border\b", r"\btrack\b", r"\bcancel\b", r"\breturn\b",
        r"\brefund\b", r"\bexchange\b", r"\bdamaged\b", r"\bmissing\b",
        r"\bshipping\b", r"\bdelivery\b", r"\bcomplaint\b", r"\bescalat",
        r"\bORD-\d{3}\b", r"\bwhere is my\b", r"\bstatus\b",
    ]
]

_SALES_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\brecommend\b", r"\bsuggest\b", r"\bcompare\b", r"\bvs\.?\b",
        r"\bbetter\b", r"\bbuy\b", r"\bprice\b", r"\bspecs?\b",
        r"\bfeatures?\b", r"\bbudget\b", r"\bcheap\b", r"\baffordable\b",
        r"\bproduct\b", r"\blooking for\b",
    ]
]

_GREETING_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"^hi\b", r"^hello\b", r"^hey\b", r"^thanks", r"^thank you",
        r"^bye\b", r"^goodbye\b", r"what can you\b", r"what do you\b",
        r"help me with",
    ]
]


def classify_intent(text: str) -> tuple[str, str]:
    """Return (decision, reasoning). Decision: support|sales|mixed|self."""
    support_hits = sum(1 for p in _SUPPORT_PATTERNS if p.search(text))
    sales_hits = sum(1 for p in _SALES_PATTERNS if p.search(text))
    greeting_hits = sum(1 for p in _GREETING_PATTERNS if p.search(text))

    if greeting_hits > 0 and support_hits == 0 and sales_hits == 0:
        return "self", f"Greeting/meta ({greeting_hits} greeting signals)"

    if support_hits > 0 and sales_hits > 0:
        return "mixed", f"Both support ({support_hits}) and sales ({sales_hits}) signals"

    if support_hits > 0:
        return "support", f"{support_hits} support signal(s) detected"

    if sales_hits > 0:
        return "sales", f"{sales_hits} sales signal(s) detected"

    return "support", "No clear signal — defaulting to support"


# -------------------------------------------------------
# Ask function
# -------------------------------------------------------
async def init_session():
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


async def ask(question: str) -> str:
    decision, reasoning = classify_intent(question)

    # Log trace
    agent_name = {
        "support": "support_agent",
        "sales": "sales_agent",
        "self": "orchestrator",
        "mixed": "support_agent → sales_agent",
    }.get(decision, "orchestrator")

    trace = tracer.start_trace(question, decision, reasoning, agent_name)
    print(f"  [{decision.upper()} → {agent_name}] {reasoning}")

    msg = types.Content(
        role="user",
        parts=[types.Part(text=question)],
    )

    response = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=msg,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response = event.content.parts[0].text or ""
            else:
                response = "I encountered an internal error. Please try again."

    tracer.end_trace(trace, response)
    return response.strip()


# -------------------------------------------------------
# Chat loop
# -------------------------------------------------------
async def chat():
    await init_session()

    print("\n" + "=" * 50)
    print(" eComBot v6 — Multi-Agent Orchestrator")
    print("=" * 50)
    if LITELLM_PROXY_ENABLED:
        print(" [Gateway Routing Enabled]")
    if MCP_ENABLED:
        print(" [FastMCP External Tools Enabled]")
    print(" Agents: Orchestrator → Support | Sales")
    print("=" * 50)
    print("Type 'exit' to quit, 'trace' to view trace report\n")

    while True:
        q = input("You: ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            tracer.print_report()
            print("Goodbye!")
            break
        if q.lower() == "trace":
            tracer.print_report()
            continue

        try:
            ans = await ask(q)
            print(f"\nAgent: {ans}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    asyncio.run(chat())
