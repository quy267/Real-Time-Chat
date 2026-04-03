"""Unit tests for Socket.IO chat event handlers (connect, join, send, leave, disconnect).

Strategy: patch src.adapters.websocket.socket_server.sio before importing handlers,
then directly call the async handler functions with a mock sio.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_sio():
    sio = AsyncMock()
    sio.save_session = AsyncMock()
    sio.get_session = AsyncMock(return_value={"user_id": "test-user-id"})
    sio.enter_room = MagicMock()
    sio.leave_room = MagicMock()
    sio.emit = AsyncMock()
    # event/on decorators must be no-ops (just return the decorated function)
    sio.event = lambda f: f
    sio.on = lambda event: (lambda f: f)
    return sio


# ---------------------------------------------------------------------------
# connect handler
# ---------------------------------------------------------------------------

class TestConnectHandler:
    @pytest.mark.asyncio
    async def test_connect_no_auth_returns_false(self, mock_sio):
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                result = await chat_events.connect("sid1", {}, None)
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_non_dict_auth_returns_false(self, mock_sio):
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                result = await chat_events.connect("sid1", {}, "bad-string")
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_empty_dict_auth_returns_false(self, mock_sio):
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                result = await chat_events.connect("sid1", {}, {})
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_missing_token_returns_false(self, mock_sio):
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                result = await chat_events.connect("sid1", {}, {"other": "value"})
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_expired_token_returns_false(self, mock_sio):
        import jwt
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                with patch.object(chat_events, "decode_token", side_effect=jwt.ExpiredSignatureError()):
                    result = await chat_events.connect("sid1", {}, {"token": "expired"})
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_invalid_token_returns_false(self, mock_sio):
        import jwt
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                with patch.object(chat_events, "decode_token", side_effect=jwt.PyJWTError()):
                    result = await chat_events.connect("sid1", {}, {"token": "bad"})
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_wrong_token_type_returns_false(self, mock_sio):
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                with patch.object(chat_events, "decode_token", return_value={"type": "refresh", "sub": "user1"}):
                    result = await chat_events.connect("sid1", {}, {"token": "tok"})
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_no_sub_in_payload_returns_false(self, mock_sio):
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                with patch.object(chat_events, "decode_token", return_value={"type": "access"}):
                    result = await chat_events.connect("sid1", {}, {"token": "tok"})
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_valid_token_saves_session(self, mock_sio):
        with patch("src.adapters.websocket.socket_server.sio", mock_sio):
            from src.adapters.websocket.event_handlers import chat_events
            with patch.object(chat_events, "sio", mock_sio):
                with patch.object(chat_events, "decode_token", return_value={"type": "access", "sub": "user-123"}):
                    result = await chat_events.connect("sid1", {}, {"token": "valid"})
        mock_sio.save_session.assert_called_once_with("sid1", {"user_id": "user-123"})
        assert result is None  # successful connect returns None (truthy in socketio)


# ---------------------------------------------------------------------------
# join_channel handler
# ---------------------------------------------------------------------------

class TestJoinChannelHandler:
    @pytest.mark.asyncio
    async def test_join_channel_non_dict_data_returns_early(self, mock_sio):
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.join_channel("sid1", "not-a-dict")
        mock_sio.enter_room.assert_not_called()

    @pytest.mark.asyncio
    async def test_join_channel_missing_channel_id_returns_early(self, mock_sio):
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.join_channel("sid1", {})
        mock_sio.enter_room.assert_not_called()

    @pytest.mark.asyncio
    async def test_join_channel_no_session_returns_early(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value=None)
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.join_channel("sid1", {"channel_id": "ch1"})
        mock_sio.enter_room.assert_not_called()

    @pytest.mark.asyncio
    async def test_join_channel_no_user_id_in_session(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={})
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.join_channel("sid1", {"channel_id": "ch1"})
        mock_sio.enter_room.assert_not_called()

    @pytest.mark.asyncio
    async def test_join_channel_success_enters_room_and_emits(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.join_channel("sid1", {"channel_id": "chan-xyz"})
        mock_sio.enter_room.assert_called_once_with("sid1", "chan-xyz")
        mock_sio.emit.assert_called_once_with(
            "user_joined",
            {"user_id": "user-abc", "channel_id": "chan-xyz"},
            room="chan-xyz",
        )


# ---------------------------------------------------------------------------
# leave_channel handler
# ---------------------------------------------------------------------------

class TestLeaveChannelHandler:
    @pytest.mark.asyncio
    async def test_leave_channel_non_dict_returns_early(self, mock_sio):
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.leave_channel("sid1", 42)
        mock_sio.leave_room.assert_not_called()

    @pytest.mark.asyncio
    async def test_leave_channel_missing_channel_id_returns_early(self, mock_sio):
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.leave_channel("sid1", {})
        mock_sio.leave_room.assert_not_called()

    @pytest.mark.asyncio
    async def test_leave_channel_success_leaves_room_and_emits(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.leave_channel("sid1", {"channel_id": "chan-xyz"})
        mock_sio.leave_room.assert_called_once_with("sid1", "chan-xyz")
        mock_sio.emit.assert_called_once_with(
            "user_left",
            {"user_id": "user-abc", "channel_id": "chan-xyz"},
            room="chan-xyz",
        )

    @pytest.mark.asyncio
    async def test_leave_channel_no_user_id_no_emit(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={})
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.leave_channel("sid1", {"channel_id": "chan-xyz"})
        mock_sio.leave_room.assert_called_once()
        mock_sio.emit.assert_not_called()


# ---------------------------------------------------------------------------
# send_message handler
# ---------------------------------------------------------------------------

class TestSendMessageHandler:
    @pytest.mark.asyncio
    async def test_send_message_non_dict_returns_early(self, mock_sio):
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.send_message("sid1", "not-dict")
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_missing_channel_id_emits_error(self, mock_sio):
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.send_message("sid1", {"content": "hello"})
        mock_sio.emit.assert_called_once_with(
            "error", {"detail": "channel_id and content are required"}, to="sid1"
        )

    @pytest.mark.asyncio
    async def test_send_message_missing_content_emits_error(self, mock_sio):
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.send_message("sid1", {"channel_id": "ch1"})
        mock_sio.emit.assert_called_once_with(
            "error", {"detail": "channel_id and content are required"}, to="sid1"
        )

    @pytest.mark.asyncio
    async def test_send_message_no_session_emits_unauthenticated(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value=None)
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.send_message("sid1", {"channel_id": "ch1", "content": "hi"})
        mock_sio.emit.assert_called_once_with(
            "error", {"detail": "Unauthenticated"}, to="sid1"
        )

    @pytest.mark.asyncio
    async def test_send_message_success_emits_to_room(self, mock_sio):
        import uuid
        from datetime import datetime, timezone

        from src.domain.entities.message import Message

        user_id = str(uuid.uuid4())
        channel_id = str(uuid.uuid4())
        msg_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        fake_message = Message(
            id=msg_id,
            content="hello world",
            channel_id=uuid.UUID(channel_id),
            user_id=uuid.UUID(user_id),
            created_at=now,
            updated_at=now,
        )

        mock_sio.get_session = AsyncMock(return_value={"user_id": user_id})

        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(return_value=fake_message)

        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            with patch("src.adapters.api.dependencies.get_send_message_use_case", return_value=mock_uc):
                await chat_events.send_message("sid1", {"channel_id": channel_id, "content": "hello world"})

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == "message_received"
        assert call_args[1]["room"] == channel_id

    @pytest.mark.asyncio
    async def test_send_message_use_case_exception_emits_error(self, mock_sio):
        import uuid
        user_id = str(uuid.uuid4())
        channel_id = str(uuid.uuid4())

        mock_sio.get_session = AsyncMock(return_value={"user_id": user_id})

        mock_uc = AsyncMock()
        mock_uc.execute = AsyncMock(side_effect=Exception("DB is down"))

        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            with patch("src.adapters.api.dependencies.get_send_message_use_case", return_value=mock_uc):
                await chat_events.send_message("sid1", {"channel_id": channel_id, "content": "hello"})

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == "error"
        assert call_args[0][1]["detail"] == "An internal error occurred"


# ---------------------------------------------------------------------------
# disconnect handler
# ---------------------------------------------------------------------------

class TestDisconnectHandler:
    @pytest.mark.asyncio
    async def test_disconnect_with_user_id_logs(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.disconnect("sid1")
        mock_sio.get_session.assert_called_once_with("sid1")

    @pytest.mark.asyncio
    async def test_disconnect_no_session(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value=None)
        from src.adapters.websocket.event_handlers import chat_events
        with patch.object(chat_events, "sio", mock_sio):
            await chat_events.disconnect("sid1")  # should not raise
        mock_sio.get_session.assert_called_once_with("sid1")
