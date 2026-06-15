import asyncio
import os
import sys
import logging

# Add parent directory to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from config.settings import (
    MODEL,
    AGENT_NAME,
    APP_NAME,
    OPENROUTER_API_KEY,
)

# reduce noise
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not set. Export it or add it to .env.")
    sys.exit(1)

# Load instruction from file
instruction_file = os.path.join(os.path.dirname(__file__), "sales_instructions_v1.txt")
with open(instruction_file, "r") as f:
    DEFAULT_INSTRUCTION = f.read().strip()


async def ask_ecom(question: str) -> str:
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id="user-1", session_id="session-1")

    agent = LlmAgent(
        name=AGENT_NAME,
        model=LiteLlm(model=MODEL),
        instruction=DEFAULT_INSTRUCTION,
    )

    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=question)],
    )

    response_text = ""
    async for event in runner.run_async(user_id="user-1", session_id="session-1", new_message=user_message):
        if event.is_final_response():
            response_text = event.content.parts[0].text or ""

    return response_text.strip()


def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Ecom question: ").strip()
        if not question:
            print("No question provided.")
            return

    try:
        answer = asyncio.run(ask_ecom(question))
    except Exception as e:
        print("Error:", e)
        return

    print("\nAgent:", answer)


if __name__ == "__main__":
    main()