"""Socket.IO typing indicator event handlers — ephemeral, no persistence."""

import logging

from src.adapters.websocket.socket_server import sio

logger = logging.getLogger(__name__)


@sio.event
async def typing_start(sid, data):
    """Broadcast typing_start to all room members when a user starts typing.

    Expected data: {"channel_id": "<uuid>"}
    """
    if not isinstance(data, dict):
        return

    channel_id = data.get("channel_id")
    if not channel_id:
        await sio.emit("error", {"detail": "channel_id is required"}, to=sid)
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        return

    await sio.emit(
        "typing_start",
        {"user_id": user_id, "channel_id": channel_id},
        room=channel_id,
        skip_sid=sid,
    )
    logger.debug("typing_start: user=%s channel=%s", user_id, channel_id)


@sio.event
async def typing_stop(sid, data):
    """Broadcast typing_stop to all room members when a user stops typing.

    Expected data: {"channel_id": "<uuid>"}
    """
    if not isinstance(data, dict):
        return

    channel_id = data.get("channel_id")
    if not channel_id:
        await sio.emit("error", {"detail": "channel_id is required"}, to=sid)
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        return

    await sio.emit(
        "typing_stop",
        {"user_id": user_id, "channel_id": channel_id},
        room=channel_id,
        skip_sid=sid,
    )
    logger.debug("typing_stop: user=%s channel=%s", user_id, channel_id)
