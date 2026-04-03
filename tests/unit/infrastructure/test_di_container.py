"""Unit tests for the DI Container in src/infrastructure/container.py."""

import pytest

from src.infrastructure.container import Container


class TestContainer:
    def test_register_and_resolve_transient(self):
        container = Container()
        container.register("thing", lambda: {"value": 42})
        result = container.resolve("thing")
        assert result == {"value": 42}

    def test_transient_creates_new_instance_each_time(self):
        container = Container()
        container.register("list", lambda: [])
        a = container.resolve("list")
        b = container.resolve("list")
        assert a is not b

    def test_singleton_returns_same_instance(self):
        container = Container()
        container.register("singleton", lambda: object(), singleton=True)
        a = container.resolve("singleton")
        b = container.resolve("singleton")
        assert a is b

    def test_singleton_factory_called_only_once(self):
        container = Container()
        call_count = {"n": 0}

        def factory():
            call_count["n"] += 1
            return object()

        container.register("once", factory, singleton=True)
        container.resolve("once")
        container.resolve("once")
        container.resolve("once")
        assert call_count["n"] == 1

    def test_resolve_unknown_key_raises_key_error(self):
        container = Container()
        with pytest.raises(KeyError):
            container.resolve("nonexistent")

    def test_multiple_registrations_independent(self):
        container = Container()
        container.register("a", lambda: 1)
        container.register("b", lambda: 2)
        assert container.resolve("a") == 1
        assert container.resolve("b") == 2

    def test_register_overwrites_previous_factory(self):
        container = Container()
        container.register("key", lambda: "first")
        container.register("key", lambda: "second")
        assert container.resolve("key") == "second"

    def test_module_level_container_instance_exists(self):
        from src.infrastructure.container import container
        assert isinstance(container, Container)

    def test_singleton_false_is_default_transient_behaviour(self):
        container = Container()
        instances = []
        container.register("item", lambda: object(), singleton=False)
        instances.append(container.resolve("item"))
        instances.append(container.resolve("item"))
        assert instances[0] is not instances[1]
