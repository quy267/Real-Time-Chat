"""Integration tests for Socket.IO messaging.

NOTE: Full end-to-end Socket.IO event testing (connect → join → send → receive)
requires a running ASGI server accessible via a real network socket, which is not
straightforward with python-socketio's AsyncClient over ASGI transport in pytest.
The AsyncClient needs an actual HTTP server (uvicorn/aiohttp), not a raw ASGI callable.

Full Socket.IO event flow tests are deferred to Phase 09 (E2E) where Docker services
provide a live uvicorn instance. The tests here verify:
  1. The socket_server module imports and initialises without errors.
  2. The sio instance is correctly typed and configured.
  3. Event handlers are registered on the sio instance.
  4. The JWT authentication logic used by on_connect is exercised directly.
"""

import pytest

from src.adapters.api.jwt_utils import create_access_token, decode_token
from src.adapters.websocket.socket_server import create_socket_app, sio

# ---------------------------------------------------------------------------
# Module-level smoke tests
# ---------------------------------------------------------------------------

def test_socket_server_imports_cleanly():
    """socket_server module loads without errors."""
    import src.adapters.websocket.socket_server as mod
    assert mod.sio is not None
    assert mod.create_socket_app is not None


def test_sio_is_async_server():
    import socketio
    assert isinstance(sio, socketio.AsyncServer)


def test_create_socket_app_returns_asgi_app():
    """create_socket_app wraps a minimal ASGI callable without raising."""
    from fastapi import FastAPI
    dummy = FastAPI()
    asgi_app = create_socket_app(dummy)
    # socketio.ASGIApp is the expected wrapper type
    import socketio
    assert isinstance(asgi_app, socketio.ASGIApp)


def test_chat_event_handlers_registered():
    """Importing chat_events registers connect/disconnect/send_message handlers."""
    import src.adapters.websocket.event_handlers.chat_events  # noqa: F401

    # python-socketio (5.x) stores handlers in .handlers {namespace: {event: fn}}
    registered = sio.handlers  # type: ignore[attr-defined]
    # Keys are namespaces; "/" is the default namespace
    default_ns = registered.get("/", {})
    for event in ("connect", "disconnect", "join_channel", "leave_channel", "send_message"):
        assert event in default_ns, f"Handler for '{event}' not registered on sio"


def test_presence_event_handlers_registered():
    """Importing presence_events registers presence_join/presence_leave handlers."""
    import src.adapters.websocket.event_handlers.presence_events  # noqa: F401

    registered = sio.handlers  # type: ignore[attr-defined]
    default_ns = registered.get("/", {})
    for event in ("presence_join", "presence_leave"):
        assert event in default_ns, f"Handler for '{event}' not registered on sio"


# ---------------------------------------------------------------------------
# JWT authentication logic (used inside on_connect)
# ---------------------------------------------------------------------------

def test_valid_access_token_decoded_correctly():
    user_id = "test-user-123"
    token = create_access_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_refresh_token_rejected_by_type_check():
    """on_connect rejects tokens where type != 'access'."""
    from src.adapters.api.jwt_utils import create_refresh_token
    token = create_refresh_token("user-abc")
    payload = decode_token(token)
    # The handler checks payload.get("type") != "access" → returns False
    assert payload.get("type") != "access"


def test_invalid_token_raises_pyjwt_error():
    import jwt
    with pytest.raises(jwt.PyJWTError):
        decode_token("not.a.valid.token")


# ---------------------------------------------------------------------------
# Presence store unit smoke
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_presence_store_set_get_online():
    from src.adapters.redis.presence_store import PresenceStore
    store = PresenceStore()
    await store.set_online("user-1", "chan-1")
    assert await store.is_online("user-1")
    users = await store.get_online_users("chan-1")
    assert "user-1" in users


@pytest.mark.asyncio
async def test_presence_store_set_offline():
    from src.adapters.redis.presence_store import PresenceStore
    store = PresenceStore()
    await store.set_online("user-2", "chan-1")
    await store.set_offline("user-2")
    assert not await store.is_online("user-2")
    assert await store.get_online_users("chan-1") == []
