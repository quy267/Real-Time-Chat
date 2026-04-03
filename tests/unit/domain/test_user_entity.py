"""Unit tests for User domain entity."""

import uuid
from datetime import datetime, timezone

from src.domain.entities.user import User


class TestUserEntity:
    def test_user_creation_with_required_fields(self):
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            username="john_doe",
            email="john@example.com",
            password_hash="hashed_pw",
        )
        assert user.id == user_id
        assert user.username == "john_doe"
        assert user.email == "john@example.com"
        assert user.password_hash == "hashed_pw"

    def test_user_default_display_name_is_none(self):
        user = User(
            id=uuid.uuid4(),
            username="jane",
            email="jane@example.com",
            password_hash="hash",
        )
        assert user.display_name is None

    def test_user_default_avatar_url_is_none(self):
        user = User(
            id=uuid.uuid4(),
            username="jane",
            email="jane@example.com",
            password_hash="hash",
        )
        assert user.avatar_url is None

    def test_user_default_status_is_offline(self):
        from src.domain.value_objects.presence_status import PresenceStatus

        user = User(
            id=uuid.uuid4(),
            username="jane",
            email="jane@example.com",
            password_hash="hash",
        )
        assert user.status == PresenceStatus.OFFLINE

    def test_user_timestamps_set_on_creation(self):
        user = User(
            id=uuid.uuid4(),
            username="tester",
            email="tester@example.com",
            password_hash="hash",
        )
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_with_all_fields(self):
        from src.domain.value_objects.presence_status import PresenceStatus

        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            username="full_user",
            email="full@example.com",
            password_hash="hash",
            display_name="Full User",
            avatar_url="https://example.com/avatar.png",
            status=PresenceStatus.ONLINE,
            created_at=now,
            updated_at=now,
        )
        assert user.display_name == "Full User"
        assert user.avatar_url == "https://example.com/avatar.png"
        assert user.status == PresenceStatus.ONLINE

    def test_user_id_is_uuid(self):
        user = User(
            id=uuid.uuid4(),
            username="uuid_user",
            email="uuid@example.com",
            password_hash="hash",
        )
        assert isinstance(user.id, uuid.UUID)
