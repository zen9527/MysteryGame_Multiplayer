from typing import Dict, Callable, Any


class Container:
    def __init__(self):
        self._services: Dict[str, tuple] = {}  # (factory, singleton)
        self._instances: Dict[str, Any] = {}

    def register(self, name: str, factory: Callable, singleton: bool = True):
        self._services[name] = (factory, singleton)

    def resolve(self, name: str) -> Any:
        if name not in self._services:
            raise ValueError(f"Service {name} not registered")
        if name in self._instances:
            return self._instances[name]
        factory, singleton = self._services[name]
        instance = factory()
        if singleton:
            self._instances[name] = instance
        return instance

    def clear(self):
        self._instances.clear()


def register_services(container):
    from server.game_manager import GameManager
    from server.websocket_hub import WebSocketHub
    from server.host_dm import HostDM
    from server.script_repository import ScriptRepository
    from server.script_service import ScriptService
    from server.llm.registry import LLMRegistry
    from server.llm.openai_provider import OpenAIProvider
    from server.config import config as app_config

    def _create_registry():
        registry = LLMRegistry()
        default = OpenAIProvider(
            name="default",
            endpoint=app_config.LLM_ENDPOINT,
            model=app_config.LLM_MODEL,
            api_key=app_config.LLM_API_KEY,
        )
        registry.register("default", default)
        return registry

    container.register("llm_registry", _create_registry, singleton=True)
    container.register("game_manager", GameManager, singleton=True)
    container.register("websocket_hub", WebSocketHub, singleton=True)
    container.register("host_dm", HostDM, singleton=True)
    container.register("script_repository", ScriptRepository, singleton=True)
    container.register("script_service", lambda: ScriptService(container.resolve("script_repository")), singleton=True)


container = Container()
