import asyncio
import os
import sys
import logging

# project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from tools.order_tools import get_order_status

from config.settings import (
    LLM_MODEL,
    LLM_BASE_URL,         
    OPENROUTER_API_KEY,
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
from tools.order_tools import get_order_status, cancel_order
from tools.product_tools import lookup_product
from tools.knowledge_tools import search_knowledge_base
from services.session_service import create_session_service

# -----------------------
# Session + Runner
# -----------------------
# Use your newly created Redis-backed session factory!
session_service = create_session_service()

USER_ID = "user-1"
SESSION_ID = "session-1"

agent = LlmAgent(
    name="ecommerce_support_agent",
    model=LiteLlm(
        model=LLM_MODEL,
        api_key=OPENROUTER_API_KEY,  # <-- Force it to use the key
        api_base=LLM_BASE_URL        # <-- Force it to use the OpenRouter URL
    ),
    instruction=DEFAULT_INSTRUCTION,
    tools=[get_order_status, cancel_order, lookup_product, search_knowledge_base],
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

    # 🔥 FIX: session must exist before first call
    await init_session()

    print("\n====================================")
    print(" E-commerce Support Agent")
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