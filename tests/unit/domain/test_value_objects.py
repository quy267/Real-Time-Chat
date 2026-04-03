"""Unit tests for domain value objects."""

import pytest

from src.domain.exceptions import ValidationError
from src.domain.value_objects.message_content import MessageContent
from src.domain.value_objects.presence_status import PresenceStatus
from src.domain.value_objects.token_pair import TokenPair


class TestMessageContent:
    def test_valid_content_created(self):
        mc = MessageContent("Hello, world!")
        assert mc.value == "Hello, world!"

    def test_empty_content_raises(self):
        with pytest.raises(ValidationError):
            MessageContent("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            MessageContent("   ")

    def test_max_length_4000_accepted(self):
        content = "a" * 4000
        mc = MessageContent(content)
        assert len(mc.value) == 4000

    def test_over_max_length_raises(self):
        content = "a" * 4001
        with pytest.raises(ValidationError):
            MessageContent(content)

    def test_str_returns_value(self):
        mc = MessageContent("test")
        assert str(mc) == "test"


class TestPresenceStatus:
    def test_online_value(self):
        assert PresenceStatus.ONLINE.value == "online"

    def test_offline_value(self):
        assert PresenceStatus.OFFLINE.value == "offline"

    def test_away_value(self):
        assert PresenceStatus.AWAY.value == "away"

    def test_dnd_value(self):
        assert PresenceStatus.DND.value == "dnd"

    def test_all_statuses_present(self):
        values = {s.value for s in PresenceStatus}
        assert values == {"online", "offline", "away", "dnd"}


class TestTokenPair:
    def test_token_pair_creation(self):
        tp = TokenPair(access_token="access123", refresh_token="refresh456")
        assert tp.access_token == "access123"
        assert tp.refresh_token == "refresh456"

    def test_token_pair_is_dataclass(self):
        tp = TokenPair(access_token="a", refresh_token="r")
        assert hasattr(tp, "access_token")
        assert hasattr(tp, "refresh_token")
