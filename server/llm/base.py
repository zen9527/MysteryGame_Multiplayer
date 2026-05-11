from abc import ABC, abstractmethod
from typing import Generator


class LLMProvider(ABC):
    """Abstract base for LLM API providers."""

    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model

    @abstractmethod
    def chat(self, messages: list[dict], temperature: float = 0.7, timeout: int = 120) -> str:
        """Send chat messages, return assistant response text."""

    @abstractmethod
    def chat_stream(self, messages: list[dict], temperature: float = 0.7) -> Generator[str, None, None]:
        """Send chat messages, yield response chunks."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Fetch available model IDs from the provider."""

    @abstractmethod
    def test_connection(self) -> str:
        """Quick connection test, returns response text."""

    def get_config(self) -> dict:
        """Return provider config summary (subclasses may override to add fields)."""
        return {
            "name": self.name,
            "type": self.provider_type,
            "model": self.model,
        }

    @property
    def provider_type(self) -> str:
        return self.__class__.__name__.replace("Provider", "").lower()
