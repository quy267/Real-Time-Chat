"""Unit tests for Socket.IO typing indicator event handlers (typing_start, typing_stop)."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_sio():
    sio = AsyncMock()
    sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
    sio.emit = AsyncMock()
    sio.event = lambda f: f
    sio.on = lambda event: (lambda f: f)
    return sio


class TestTypingStartHandler:
    @pytest.mark.asyncio
    async def test_typing_start_non_dict_returns_early(self, mock_sio):
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_start("sid1", "not-a-dict")
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_typing_start_missing_channel_id_emits_error(self, mock_sio):
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_start("sid1", {})
        mock_sio.emit.assert_called_once_with(
            "error", {"detail": "channel_id is required"}, to="sid1"
        )

    @pytest.mark.asyncio
    async def test_typing_start_no_session_returns_early(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value=None)
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_start("sid1", {"channel_id": "ch1"})
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_typing_start_no_user_id_in_session_returns_early(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={})
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_start("sid1", {"channel_id": "ch1"})
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_typing_start_success_broadcasts_to_room(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_start("sid1", {"channel_id": "ch-xyz"})
        mock_sio.emit.assert_called_once_with(
            "typing_start",
            {"user_id": "user-abc", "channel_id": "ch-xyz"},
            room="ch-xyz",
            skip_sid="sid1",
        )


class TestTypingStopHandler:
    @pytest.mark.asyncio
    async def test_typing_stop_non_dict_returns_early(self, mock_sio):
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_stop("sid1", [])
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_typing_stop_missing_channel_id_emits_error(self, mock_sio):
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_stop("sid1", {})
        mock_sio.emit.assert_called_once_with(
            "error", {"detail": "channel_id is required"}, to="sid1"
        )

    @pytest.mark.asyncio
    async def test_typing_stop_no_session_returns_early(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value=None)
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_stop("sid1", {"channel_id": "ch1"})
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_typing_stop_no_user_id_in_session_returns_early(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={})
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_stop("sid1", {"channel_id": "ch1"})
        mock_sio.emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_typing_stop_success_broadcasts_to_room(self, mock_sio):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import typing_events
        with patch.object(typing_events, "sio", mock_sio):
            await typing_events.typing_stop("sid1", {"channel_id": "ch-xyz"})
        mock_sio.emit.assert_called_once_with(
            "typing_stop",
            {"user_id": "user-abc", "channel_id": "ch-xyz"},
            room="ch-xyz",
            skip_sid="sid1",
        )
