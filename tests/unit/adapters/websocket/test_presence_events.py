"""Unit tests for Socket.IO presence event handlers (presence_join, presence_leave)."""

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


@pytest.fixture
def mock_presence_store():
    store = AsyncMock()
    store.set_online = AsyncMock()
    store.set_offline = AsyncMock()
    return store


class TestPresenceJoinHandler:
    @pytest.mark.asyncio
    async def test_presence_join_non_dict_returns_early(self, mock_sio, mock_presence_store):
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_join("sid1", "not-a-dict")
        mock_presence_store.set_online.assert_not_called()

    @pytest.mark.asyncio
    async def test_presence_join_missing_channel_id_returns_early(self, mock_sio, mock_presence_store):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_join("sid1", {})
        mock_presence_store.set_online.assert_not_called()

    @pytest.mark.asyncio
    async def test_presence_join_no_session_returns_early(self, mock_sio, mock_presence_store):
        mock_sio.get_session = AsyncMock(return_value=None)
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_join("sid1", {"channel_id": "ch1"})
        mock_presence_store.set_online.assert_not_called()

    @pytest.mark.asyncio
    async def test_presence_join_no_user_id_in_session_returns_early(self, mock_sio, mock_presence_store):
        mock_sio.get_session = AsyncMock(return_value={})
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_join("sid1", {"channel_id": "ch1"})
        mock_presence_store.set_online.assert_not_called()

    @pytest.mark.asyncio
    async def test_presence_join_success_sets_online_and_emits(self, mock_sio, mock_presence_store):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_join("sid1", {"channel_id": "ch-xyz"})
        mock_presence_store.set_online.assert_called_once_with("user-abc", "ch-xyz")
        mock_sio.emit.assert_called_once_with(
            "user_online",
            {"user_id": "user-abc", "channel_id": "ch-xyz"},
            room="ch-xyz",
        )


class TestPresenceLeaveHandler:
    @pytest.mark.asyncio
    async def test_presence_leave_non_dict_returns_early(self, mock_sio, mock_presence_store):
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_leave("sid1", 99)
        mock_presence_store.set_offline.assert_not_called()

    @pytest.mark.asyncio
    async def test_presence_leave_no_session_returns_early(self, mock_sio, mock_presence_store):
        mock_sio.get_session = AsyncMock(return_value=None)
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_leave("sid1", {"channel_id": "ch1"})
        mock_presence_store.set_offline.assert_not_called()

    @pytest.mark.asyncio
    async def test_presence_leave_no_user_id_in_session_returns_early(self, mock_sio, mock_presence_store):
        mock_sio.get_session = AsyncMock(return_value={})
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_leave("sid1", {"channel_id": "ch1"})
        mock_presence_store.set_offline.assert_not_called()

    @pytest.mark.asyncio
    async def test_presence_leave_with_channel_id_emits_offline(self, mock_sio, mock_presence_store):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_leave("sid1", {"channel_id": "ch-xyz"})
        mock_presence_store.set_offline.assert_called_once_with("user-abc")
        mock_sio.emit.assert_called_once_with(
            "user_offline",
            {"user_id": "user-abc", "channel_id": "ch-xyz"},
            room="ch-xyz",
        )

    @pytest.mark.asyncio
    async def test_presence_leave_without_channel_id_no_emit(self, mock_sio, mock_presence_store):
        mock_sio.get_session = AsyncMock(return_value={"user_id": "user-abc"})
        from src.adapters.websocket.event_handlers import presence_events
        with patch.object(presence_events, "sio", mock_sio):
            with patch.object(presence_events, "get_presence_store", return_value=mock_presence_store):
                await presence_events.on_presence_leave("sid1", {})
        mock_presence_store.set_offline.assert_called_once_with("user-abc")
        mock_sio.emit.assert_not_called()


class TestPresenceStoreDependencyInjection:
    def test_set_presence_store_replaces_store(self):
        from src.adapters.redis.presence_store import PresenceStore
        from src.adapters.websocket.event_handlers import presence_events

        custom_store = PresenceStore()
        presence_events.set_presence_store(custom_store)
        assert presence_events.get_presence_store() is custom_store
        # Reset to None so lazy init works in other tests
        presence_events._presence_store = None

    def test_get_presence_store_lazy_init(self):
        from src.adapters.websocket.event_handlers import presence_events
        presence_events._presence_store = None
        store = presence_events.get_presence_store()
        assert store is not None
        # Cleanup
        presence_events._presence_store = None
