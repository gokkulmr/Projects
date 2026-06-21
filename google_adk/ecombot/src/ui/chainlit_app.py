"""eComBot v7 — Chainlit Generative UI.

Run with: chainlit run src/ui/chainlit_app.py -w
"""

import os
import sys

# project path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import chainlit as cl

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from config.settings import (
    LLM_MODEL,
    LLM_BASE_URL,
    OPENROUTER_API_KEY,
    LITELLM_PROXY_ENABLED,
    MCP_ENABLED,
)

os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

# -------------------------------------------------------
# Load instructions
# -------------------------------------------------------
def _load_instructions(filename: str) -> str:
    agents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agents")
    path = os.path.join(agents_dir, filename)
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
# Agents
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

orchestrator = LlmAgent(
    name="ecombot_orchestrator",
    model=llm_model,
    instruction=ORCHESTRATOR_INSTRUCTIONS,
    sub_agents=[support_agent, sales_agent],
    description="Central coordinator that routes queries to Support or Sales agents.",
)

APP_NAME = "ecombot-v7-chainlit"

# Card renderers
from ui.card_renderers import render_order_card, render_product_card, render_stock_card


# -------------------------------------------------------
# Chainlit lifecycle
# -------------------------------------------------------
@cl.on_chat_start
async def on_start():
    """Initialize session when a new chat starts."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id="chainlit-user",
        session_id="chainlit-session",
    )

    runner = Runner(
        agent=orchestrator,
        app_name=APP_NAME,
        session_service=session_service,
    )

    cl.user_session.set("runner", runner)
    cl.user_session.set("session_service", session_service)
    cl.user_session.set("user_id", "chainlit-user")
    cl.user_session.set("session_id", "chainlit-session")
    cl.user_session.set("last_order_id", None)
    cl.user_session.set("last_product", None)

    await cl.Message(
        content=(
            "👋 **Welcome to eComBot!**\n\n"
            "I can help you with:\n"
            "- 📦 **Order tracking & support** — check status, cancel orders, returns\n"
            "- 🛍️ **Product recommendations** — compare products, find deals\n"
            "- ❓ **FAQ & policies** — shipping, warranties, payment methods\n\n"
            "How can I help you today?"
        ),
        actions=[
            cl.Action(name="quick_order", payload={"value": "check_order"}, label="📦 Check Order Status"),
            cl.Action(name="quick_products", payload={"value": "browse_products"}, label="🛍️ Browse Products"),
            cl.Action(name="quick_faq", payload={"value": "faq"}, label="❓ FAQ & Policies"),
        ],
    ).send()


@cl.action_callback("quick_order")
async def on_quick_order(action: cl.Action):
    """Handle quick order check button."""
    await cl.Message(content="Sure! Please provide your order ID (e.g., ORD-001).").send()


@cl.action_callback("quick_products")
async def on_quick_products(action: cl.Action):
    """Handle quick product browse button."""
    await process_message("What products do you have available?")


@cl.action_callback("quick_faq")
async def on_quick_faq(action: cl.Action):
    """Handle quick FAQ button."""
    await cl.Message(
        content="What would you like to know about?",
        actions=[
            cl.Action(name="faq_topic", payload={"value": "return policy"}, label="📋 Return Policy"),
            cl.Action(name="faq_topic", payload={"value": "shipping options"}, label="🚚 Shipping"),
            cl.Action(name="faq_topic", payload={"value": "warranty information"}, label="🛡️ Warranty"),
            cl.Action(name="faq_topic", payload={"value": "payment methods"}, label="💳 Payment Methods"),
        ],
    ).send()


@cl.action_callback("faq_topic")
async def on_faq_topic(action: cl.Action):
    """Handle FAQ topic selection."""
    topic = action.payload.get("value", "FAQ")
    await process_message(f"What is your {topic}?")


@cl.action_callback("budget_select")
async def on_budget_select(action: cl.Action):
    """Handle budget selection for product recommendations."""
    budget = action.payload.get("value", "any")
    await process_message(f"Recommend products under ₹{budget}")


async def process_message(question: str):
    """Core message processing with tool-call step visualization."""
    runner = cl.user_session.get("runner")
    user_id = cl.user_session.get("user_id")
    session_id = cl.user_session.get("session_id")

    msg = types.Content(
        role="user",
        parts=[types.Part(text=question)],
    )

    response_text = ""
    tool_calls_seen = []

    # Create a step for agent processing
    async with cl.Step(name="🤖 Processing", type="run") as step:
        step.input = question

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=msg,
        ):
            # Track tool calls for step visualization
            if event.get_function_calls():
                for fc in event.get_function_calls():
                    tool_calls_seen.append({
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    })

            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text or ""
                else:
                    response_text = "I encountered an issue. Please try again."

        step.output = response_text[:200]

    # Show tool call steps
    for tc in tool_calls_seen:
        tool_name = tc["name"]
        tool_args = tc["args"]
        step_name = {
            "get_order_status": "📦 Checking Order Status",
            "cancel_order": "❌ Cancelling Order",
            "lookup_product": "🔍 Searching Products",
            "search_knowledge_base": "📚 Searching Knowledge Base",
            "mcp_get_order_status": "📦 Checking Order (MCP)",
            "mcp_cancel_order": "❌ Cancelling Order (MCP)",
            "mcp_check_stock": "📊 Checking Stock (MCP)",
            "mcp_list_variants": "🎨 Listing Variants (MCP)",
        }.get(tool_name, f"🔧 {tool_name}")

        async with cl.Step(name=step_name, type="tool") as tool_step:
            tool_step.input = str(tool_args)
            tool_step.output = "Completed"

    # Detect and store context in session
    import re
    order_match = re.search(r"ORD-\d{3}", question)
    if order_match:
        cl.user_session.set("last_order_id", order_match.group())

    # Send the final response
    elements = []

    # Add action buttons for follow-ups based on context
    actions = []
    last_order = cl.user_session.get("last_order_id")
    if last_order and any(kw in question.lower() for kw in ["order", "track", "status"]):
        actions.extend([
            cl.Action(name="followup_action", payload={"value": f"Cancel order {last_order}"}, label=f"❌ Cancel {last_order}"),
            cl.Action(name="followup_action", payload={"value": f"What is the return policy?"}, label="📋 Return Policy"),
        ])

    if any(kw in question.lower() for kw in ["recommend", "product", "suggest", "compare", "buy"]):
        actions.extend([
            cl.Action(name="budget_select", payload={"value": "3000"}, label="💰 Under ₹3,000"),
            cl.Action(name="budget_select", payload={"value": "5000"}, label="💰 Under ₹5,000"),
            cl.Action(name="budget_select", payload={"value": "10000"}, label="💰 Under ₹10,000"),
        ])

    await cl.Message(
        content=response_text.strip(),
        actions=actions if actions else None,
    ).send()


@cl.action_callback("followup_action")
async def on_followup(action: cl.Action):
    """Handle follow-up action buttons."""
    query = action.payload.get("value", "")
    await process_message(query)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming user messages."""
    await process_message(message.content)
