"""Dependency injection container — wires repositories, use cases, and services."""


class Container:
    """Simple DI container for wiring application dependencies.

    Providers are registered as factory functions and resolved lazily.
    """

    def __init__(self) -> None:
        self._factories: dict = {}
        self._singletons: dict = {}

    def register(self, key: str, factory, singleton: bool = False) -> None:
        self._factories[key] = (factory, singleton)

    def resolve(self, key: str):
        factory, singleton = self._factories[key]
        if singleton:
            if key not in self._singletons:
                self._singletons[key] = factory()
            return self._singletons[key]
        return factory()


container = Container()
