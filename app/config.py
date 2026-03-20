import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# GHL
GHL_API_TOKEN = os.environ["GHL_API_TOKEN"]
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "Fb5Ou7RWrtKsYxqwKByc")
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"

# Webhook Security
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

# Defaults (overridden by bot_config table)
DEFAULT_DEBOUNCE_SECONDS = 15
DEFAULT_QUALIFICATION_THRESHOLD = 6
DEFAULT_CONTEXT_MESSAGES = 20
