"""Socket.IO server factory — wraps FastAPI as an ASGI app."""

import socketio

from src.infrastructure.config import settings

# Build allowed origins from settings: "*" means all, otherwise split CSV
_cors_origins = (
    settings.cors_origins.split(",")
    if settings.cors_origins != "*"
    else "*"
)

# Single server instance shared across event handler modules
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=_cors_origins,
    # Redis manager can be enabled for multi-instance:
    # client_manager=socketio.AsyncRedisManager(settings.redis_url)
)


def create_socket_app(fastapi_app):
    """Return an ASGI app: Socket.IO wrapping FastAPI.

    Socket.IO handles /socket.io/* requests; all others pass through to FastAPI.
    """
    return socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
