import asyncio
import os
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

# Force the API key into the environment for LiteLLM
os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

# -----------------------
# Logging cleanup
# -----------------------
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not set")
    sys.exit(1)

# -----------------------
# Instructions
# -----------------------
instruction_file = os.path.join(
    os.path.dirname(__file__),
    "support_instructions_v1.txt"
)

with open(instruction_file, "r", encoding="utf-8") as f:
    DEFAULT_INSTRUCTION = f.read().strip()

# -----------------------
# Session + Runner
# -----------------------
from services.session_service import create_session_service

# Gateway routing
from gateway.proxy_client import GatewayClient
from gateway.router import QueryRouter

# Tools
from tools.order_tools import get_order_status, cancel_order
from tools.product_tools import lookup_product
from tools.knowledge_tools import search_knowledge_base
from tools.mcp_order_tools import mcp_get_order_status, mcp_get_order_details, mcp_cancel_order, mcp_check_stock, mcp_list_variants

# Select tools based on MCP enabled flag
if MCP_ENABLED:
    tools_list = [
        mcp_get_order_status,
        mcp_get_order_details,
        mcp_cancel_order,
        mcp_check_stock,
        mcp_list_variants,
        search_knowledge_base
    ]
else:
    tools_list = [
        get_order_status, 
        cancel_order, 
        lookup_product, 
        search_knowledge_base
    ]

# Select model based on Gateway enabled flag
if LITELLM_PROXY_ENABLED:
    gateway_client = GatewayClient()
    llm_model = gateway_client.create_gateway_model()
    query_router = QueryRouter()
else:
    llm_model = LiteLlm(
        model=LLM_MODEL,
        api_key=OPENROUTER_API_KEY,
        api_base=LLM_BASE_URL
    )
    query_router = None

session_service = create_session_service()
USER_ID = "user-1"
SESSION_ID = "session-1"

agent = LlmAgent(
    name="ecommerce_support_agent",
    model=llm_model,
    instruction=DEFAULT_INSTRUCTION,
    tools=tools_list,
)

APP_NAME = "ecom-support-agent"

runner = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service,
)


# -----------------------
# IMPORTANT: create session
# -----------------------
async def init_session():
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

# -----------------------
# Ask function
# -----------------------
async def ask_ecom(question: str) -> str:
    # 1. Day 7 Routing: classify intent if Gateway is enabled
    route_hint = None
    if LITELLM_PROXY_ENABLED and query_router:
        decision = query_router.classify(question)
        route_hint = decision.route_hint
        # We can pass route_hint to Litellm via metadata but Google ADK doesn't expose it directly yet
        # So we log it and gateway client handles it internally where possible
        print(f"[{decision.route_hint} route selected: {decision.reasoning}]")

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
            # Safely check if content and parts exist before reading
            if event.content and event.content.parts:
                response = event.content.parts[0].text or ""
            else:
                response = "I encountered an internal error. Please try again."

    return response.strip()

# -----------------------
# Chat loop
# -----------------------
async def chat():
    await init_session()

    print("\n====================================")
    print(" E-commerce Support Agent")
    if LITELLM_PROXY_ENABLED:
        print(" [Gateway Routing Enabled]")
    if MCP_ENABLED:
        print(" [FastMCP External Tools Enabled]")
    print("====================================")
    print("Type 'exit' to quit\n")

    while True:
        q = input("You: ").strip()

        if not q:
            continue

        if q.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        try:
            ans = await ask_ecom(q)
            print(f"\nAgent: {ans}\n")
        except Exception as e:
            print(f"\nError: {e}\n")

# -----------------------
# Main
# -----------------------
if __name__ == "__main__":
    asyncio.run(chat())