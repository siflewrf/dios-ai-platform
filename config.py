import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-4o-mini"

# Request Configuration
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = 2  # seconds between retries

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validation
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set. Create .env file with your API key.")
