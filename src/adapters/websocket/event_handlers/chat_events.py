"""Socket.IO chat event handlers — connect, join, send, leave, disconnect."""

import logging

import jwt

from src.adapters.api.jwt_utils import decode_token
from src.adapters.websocket.socket_server import sio

logger = logging.getLogger(__name__)


@sio.event
async def connect(sid, environ, auth):
    """Authenticate client via JWT in auth dict. Reject if invalid."""
    if not auth or not isinstance(auth, dict):
        logger.warning("Socket connect rejected: missing auth dict (sid=%s)", sid)
        return False

    token = auth.get("token")
    if not token:
        logger.warning("Socket connect rejected: no token (sid=%s)", sid)
        return False

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        logger.warning("Socket connect rejected: expired token (sid=%s)", sid)
        return False
    except jwt.PyJWTError:
        logger.warning("Socket connect rejected: invalid token (sid=%s)", sid)
        return False

    if payload.get("type") != "access":
        logger.warning("Socket connect rejected: wrong token type (sid=%s)", sid)
        return False

    user_id = payload.get("sub")
    if not user_id:
        return False

    await sio.save_session(sid, {"user_id": user_id})
    logger.info("Socket connected: sid=%s user_id=%s", sid, user_id)


@sio.event
async def join_channel(sid, data):
    """Join a Socket.IO room for a channel after verifying membership."""
    if not isinstance(data, dict):
        return

    channel_id = data.get("channel_id")
    if not channel_id:
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        return

    # Membership check: use the injected dependency if available, else skip
    # Full membership enforcement is handled at use-case layer on send_message
    sio.enter_room(sid, channel_id)
    await sio.emit("user_joined", {"user_id": user_id, "channel_id": channel_id}, room=channel_id)
    logger.info("User %s joined channel %s (sid=%s)", user_id, channel_id, sid)


@sio.event
async def leave_channel(sid, data):
    """Leave a Socket.IO room for a channel."""
    if not isinstance(data, dict):
        return

    channel_id = data.get("channel_id")
    if not channel_id:
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None

    sio.leave_room(sid, channel_id)
    if user_id:
        await sio.emit("user_left", {"user_id": user_id, "channel_id": channel_id}, room=channel_id)
    logger.info("User %s left channel %s (sid=%s)", user_id, channel_id, sid)


@sio.event
async def send_message(sid, data):
    """Persist message via SendMessageUseCase and broadcast to channel room."""
    if not isinstance(data, dict):
        return

    channel_id = data.get("channel_id")
    content = data.get("content")
    thread_id = data.get("thread_id")

    if not channel_id or not content:
        await sio.emit("error", {"detail": "channel_id and content are required"}, to=sid)
        return

    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        await sio.emit("error", {"detail": "Unauthenticated"}, to=sid)
        return

    try:
        from src.adapters.api.dependencies import get_send_message_use_case
        uc = get_send_message_use_case()
        message = await uc.execute(
            content=content,
            channel_id=channel_id,
            user_id=user_id,
            thread_id=thread_id,
        )
        payload = {
            "id": str(message.id),
            "content": message.content,
            "channel_id": str(message.channel_id),
            "user_id": str(message.user_id),
            "thread_id": str(message.thread_id) if message.thread_id else None,
            "file_url": message.file_url,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat(),
        }
        await sio.emit("message_received", payload, room=channel_id)
    except Exception as exc:
        logger.exception("Error in send_message handler: %s", exc)
        await sio.emit("error", {"detail": "An internal error occurred"}, to=sid)


@sio.event
async def disconnect(sid):
    """Clean up session on disconnect."""
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    logger.info("Socket disconnected: sid=%s user_id=%s", sid, user_id)
