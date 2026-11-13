"""All settings in one place.

Values come from environment variables. Locally they are read from a `.env` file.
On Streamlit Community Cloud, top-level secrets are exposed as environment variables too.
"""
import os

try:  # python-dotenv is optional: only used when running on your own computer
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Which LLM to use, in LangChain's "provider:model" format.
# Change it without touching code, e.g. MODEL="google_genai:gemini-3.6-flash"
MODEL = os.getenv("MODEL", "google_genai:gemini-3.8-flash")

# Backup models, tried in order if the main one is overloaded (503) or fails.
FALLBACK_MODELS = [m.strip() for m in os.getenv(
    "FALLBACK_MODELS", "google_genai:gemini-3.6-flash,google_genai:gemini-3.5-flash-lite"
).split(",") if m.strip() and m.strip() != MODEL]

# Embedding model used to turn text into vectors (runs locally, no API key needed).
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# How many knowledge-base passages to retrieve per search.
TOP_K = int(os.getenv("TOP_K", "4"))


def has_llm_key() -> bool:
    """True if a Gemini API key is available (LangChain accepts either name)."""
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
