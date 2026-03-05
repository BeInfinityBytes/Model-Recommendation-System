"""
Application settings loaded from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
from dotenv import load_dotenv
import os

# -----------------------------------------------------
# Load .env from project ROOT (where uvicorn is run)
# -----------------------------------------------------

CURRENT_DIR = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_DIR.parents[3]
ENV_PATH = PROJECT_ROOT / ".env"

print(f"[DEBUG] settings.py location: {CURRENT_DIR}")
print(f"[DEBUG] project root resolved as: {PROJECT_ROOT}")
print(f"[DEBUG] checking .env at: {ENV_PATH}")

if ENV_PATH.exists():
    print("[DEBUG] .env FOUND. Loading...")
    load_dotenv(ENV_PATH)
else:
    print(f"[ERROR] .env NOT FOUND at: {ENV_PATH}")


class Settings(BaseSettings):
    # Logging
    LOG_LEVEL: str = Field("INFO")

    # --- USECASE SESSION DB (Now Remote Atlas) ---
    MONGODB_URI: str
    MONGODB_DB: str
    MONGODB_COLLECTION: str     # <--- ADDED

    # --- Remote Scraped Model DB ---
    MODEL_DATA_MONGO_URI: str
    MODEL_DATA_DB: str
    MODEL_DATA_COLLECTION: str

    # Gemini
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = Field("models/gemini-2.0-flash")
    
     # --- LLM / Embeddings ---
    OPENAI_API_KEY: str | None = None

    # --- Pinecone ---
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        extra="ignore"
    )


settings = Settings()

print("\n========== SETTINGS LOADED SUCCESSFULLY ==========")
print("MONGODB_URI =", settings.MONGODB_URI)
print("MONGODB_DB =", settings.MONGODB_DB)
print("MONGODB_COLLECTION =", settings.MONGODB_COLLECTION)
print("MODEL_DATA_MONGO_URI =", settings.MODEL_DATA_MONGO_URI)
print("MODEL_DATA_DB =", settings.MODEL_DATA_DB)
print("MODEL_DATA_COLLECTION =", settings.MODEL_DATA_COLLECTION)
print("GEMINI_MODEL =", settings.GEMINI_MODEL)
print("=================================================\n")
