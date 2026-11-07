import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

OPEN_LIBRARY_BASE_URL = os.getenv(
    "OPEN_LIBRARY_BASE_URL",
    "https://openlibrary.org",
)

OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1",
)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

GOOGLE_VISION_FALLBACK_ENABLED = (
    os.getenv("GOOGLE_VISION_FALLBACK_ENABLED", "false").strip().lower()
    == "true"
)
SCAN_RATE_LIMIT = os.getenv(
    "SCAN_RATE_LIMIT",
    "3/minute;20/hour",
)


@lru_cache(maxsize=1)
def get_openrouter_client() -> OpenAI:
    """Create the API client only when image detection needs it."""
    if not OPENROUTER_API_KEY:
        raise ValueError("Set OPENROUTER_API_KEY in the environment or project .env file.")

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )
