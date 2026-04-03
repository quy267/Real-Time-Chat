"""Integration tests for typing indicator Socket.IO event handlers."""

import importlib


def test_typing_events_module_importable():
    """Ensure typing_events module loads without errors."""
    mod = importlib.import_module(
        "src.adapters.websocket.event_handlers.typing_events"
    )
    assert mod is not None


def test_typing_start_handler_registered():
    """Verify typing_start handler is registered on the sio instance."""
    import src.adapters.websocket.event_handlers.typing_events  # noqa: F401
    from src.adapters.websocket.socket_server import sio

    # python-socketio stores handlers in _event_handlers dict
    handlers = getattr(sio, "_event_handlers", {})
    # Also check namespace handlers
    ns_handlers = getattr(sio, "handlers", {})
    registered = (
        "typing_start" in handlers
        or any("typing_start" in h for h in ns_handlers.values())
    )
    assert registered, "typing_start event not registered on sio"


def test_typing_stop_handler_registered():
    """Verify typing_stop handler is registered on the sio instance."""
    import src.adapters.websocket.event_handlers.typing_events  # noqa: F401
    from src.adapters.websocket.socket_server import sio

    handlers = getattr(sio, "_event_handlers", {})
    ns_handlers = getattr(sio, "handlers", {})
    registered = (
        "typing_stop" in handlers
        or any("typing_stop" in h for h in ns_handlers.values())
    )
    assert registered, "typing_stop event not registered on sio"
