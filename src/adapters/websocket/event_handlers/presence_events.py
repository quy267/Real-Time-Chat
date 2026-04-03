"""Socket.IO presence event handlers — broadcast online/offline status changes."""

import logging

from src.adapters.redis.presence_store import PresenceStore
from src.adapters.websocket.socket_server import sio

logger = logging.getLogger(__name__)

# Module-level presence store — replaced in tests via dependency injection pattern
_presence_store: PresenceStore | None = None


def get_presence_store() -> PresenceStore:
    global _presence_store
    if _presence_store is None:
        _presence_store = PresenceStore()
    return _presence_store


def set_presence_store(store: PresenceStore) -> None:
    """Allow tests and DI to inject a custom presence store."""
    global _presence_store
    _presence_store = store


@sio.on("presence_join")
async def on_presence_join(sid, data):
    """Track user as online in a channel and broadcast status."""
    if not isinstance(data, dict):
        return

    channel_id = data.get("channel_id")
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id or not channel_id:
        return

    store = get_presence_store()
    await store.set_online(user_id, channel_id)
    await sio.emit(
        "user_online",
        {"user_id": user_id, "channel_id": channel_id},
        room=channel_id,
    )
    logger.info("Presence online: user=%s channel=%s", user_id, channel_id)


@sio.on("presence_leave")
async def on_presence_leave(sid, data):
    """Mark user offline and broadcast status."""
    if not isinstance(data, dict):
        return

    channel_id = data.get("channel_id")
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        return

    store = get_presence_store()
    await store.set_offline(user_id)
    if channel_id:
        await sio.emit(
            "user_offline",
            {"user_id": user_id, "channel_id": channel_id},
            room=channel_id,
        )
    logger.info("Presence offline: user=%s", user_id)
