import os
from dotenv import load_dotenv

load_dotenv()  # load OPENROUTER_API_KEY from .env if present

# Provider / model
MODEL = "openrouter/google/gemini-2.5-flash"

# App / agent config
APP_NAME = "ecombot"
AGENT_NAME = "ecom_support_agent"


# API key expected by litellm / openrouter integration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")