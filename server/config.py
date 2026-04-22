import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "http://127.0.0.1:12340")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3.5-122b-a10b")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

config = Config()
