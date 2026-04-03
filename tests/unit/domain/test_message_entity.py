"""Unit tests for Message domain entity."""

import uuid
from datetime import datetime

from src.domain.entities.message import Message


class TestMessageEntity:
    def test_message_creation_with_required_fields(self):
        msg_id = uuid.uuid4()
        channel_id = uuid.uuid4()
        user_id = uuid.uuid4()
        msg = Message(
            id=msg_id,
            content="Hello world",
            channel_id=channel_id,
            user_id=user_id,
        )
        assert msg.id == msg_id
        assert msg.content == "Hello world"
        assert msg.channel_id == channel_id
        assert msg.user_id == user_id

    def test_message_optional_thread_id_defaults_none(self):
        msg = Message(
            id=uuid.uuid4(),
            content="Hi",
            channel_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        assert msg.thread_id is None

    def test_message_optional_file_url_defaults_none(self):
        msg = Message(
            id=uuid.uuid4(),
            content="Hi",
            channel_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        assert msg.file_url is None

    def test_message_with_thread_id(self):
        thread_id = uuid.uuid4()
        msg = Message(
            id=uuid.uuid4(),
            content="Thread reply",
            channel_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            thread_id=thread_id,
        )
        assert msg.thread_id == thread_id

    def test_message_with_file_url(self):
        msg = Message(
            id=uuid.uuid4(),
            content="See file",
            channel_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            file_url="https://example.com/file.png",
        )
        assert msg.file_url == "https://example.com/file.png"

    def test_message_timestamps_set_on_creation(self):
        msg = Message(
            id=uuid.uuid4(),
            content="Timestamped",
            channel_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        assert isinstance(msg.created_at, datetime)
        assert isinstance(msg.updated_at, datetime)

    def test_message_id_is_uuid(self):
        msg = Message(
            id=uuid.uuid4(),
            content="UUID check",
            channel_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        assert isinstance(msg.id, uuid.UUID)
        assert isinstance(msg.channel_id, uuid.UUID)
        assert isinstance(msg.user_id, uuid.UUID)
