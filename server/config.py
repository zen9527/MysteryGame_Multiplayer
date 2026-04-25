import os
from dotenv import load_dotenv

# Load .env from project root (same directory as server/ when run from project root)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

class Config:
    LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "http://127.0.0.1:12340")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen/qwen3.6-27b")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

config = Config()
