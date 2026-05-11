import logging
from server.llm.base import LLMProvider

log = logging.getLogger(__name__)


class LLMRegistry:
    """Manages multiple LLM providers with active selection."""

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._active_name: str | None = None

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name] = provider
        if self._active_name is None:
            self._active_name = name
            log.info(f"[LLMRegistry] Registered '{name}' as active provider ({provider.provider_type})")
        else:
            log.info(f"[LLMRegistry] Registered '{name}' ({provider.provider_type})")

    def remove(self, name: str) -> None:
        if name not in self._providers:
            return
        del self._providers[name]
        if self._active_name == name:
            self._active_name = next(iter(self._providers), None)
        log.info(f"[LLMRegistry] Removed provider '{name}'")

    def set_active(self, name: str) -> None:
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        self._active_name = name
        log.info(f"[LLMRegistry] Active provider set to '{name}'")

    def get_active(self) -> LLMProvider:
        if not self._active_name or self._active_name not in self._providers:
            raise ValueError("No providers registered")
        return self._providers[self._active_name]

    def get(self, name: str) -> LLMProvider:
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        return self._providers[name]

    def list_providers(self) -> list[dict]:
        result = []
        for name, provider in self._providers.items():
            config = provider.get_config()
            config["is_active"] = (name == self._active_name)
            result.append(config)
        return result

    def create_provider(self, provider_type: str, name: str, **kwargs) -> LLMProvider:
        endpoint = kwargs.get("endpoint", "")
        model = kwargs.get("model", "")
        api_key = kwargs.get("api_key", "")

        if provider_type == "openai":
            from server.llm.openai_provider import OpenAIProvider
            return OpenAIProvider(name, endpoint, model, api_key)
        elif provider_type == "anthropic":
            from server.llm.anthropic_provider import AnthropicProvider
            return AnthropicProvider(name, endpoint, model, api_key)
        elif provider_type == "gemini":
            from server.llm.gemini_provider import GeminiProvider
            return GeminiProvider(name, endpoint, model, api_key)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
