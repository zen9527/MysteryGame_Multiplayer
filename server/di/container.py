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
    from server.llm_client import LLMClient

    container.register("llm_client", LLMClient)
    container.register("game_manager", GameManager, singleton=True)
    container.register("websocket_hub", WebSocketHub, singleton=True)
    container.register("host_dm", HostDM, singleton=True)


container = Container()
