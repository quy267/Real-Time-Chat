"""Unit tests for Channel domain entity."""

import uuid
from datetime import datetime

from src.domain.entities.channel import Channel, ChannelType


class TestChannelEntity:
    def test_channel_creation_with_required_fields(self):
        channel_id = uuid.uuid4()
        creator_id = uuid.uuid4()
        channel = Channel(
            id=channel_id,
            name="general",
            creator_id=creator_id,
        )
        assert channel.id == channel_id
        assert channel.name == "general"
        assert channel.creator_id == creator_id

    def test_channel_default_type_is_public(self):
        channel = Channel(
            id=uuid.uuid4(),
            name="public-channel",
            creator_id=uuid.uuid4(),
        )
        assert channel.channel_type == ChannelType.PUBLIC

    def test_channel_private_type(self):
        channel = Channel(
            id=uuid.uuid4(),
            name="private-channel",
            creator_id=uuid.uuid4(),
            channel_type=ChannelType.PRIVATE,
        )
        assert channel.channel_type == ChannelType.PRIVATE

    def test_channel_default_description_is_none(self):
        channel = Channel(
            id=uuid.uuid4(),
            name="no-desc",
            creator_id=uuid.uuid4(),
        )
        assert channel.description is None

    def test_channel_with_description(self):
        channel = Channel(
            id=uuid.uuid4(),
            name="described",
            creator_id=uuid.uuid4(),
            description="A channel with a description",
        )
        assert channel.description == "A channel with a description"

    def test_channel_timestamps_set_on_creation(self):
        channel = Channel(
            id=uuid.uuid4(),
            name="timestamped",
            creator_id=uuid.uuid4(),
        )
        assert isinstance(channel.created_at, datetime)
        assert isinstance(channel.updated_at, datetime)

    def test_channel_type_enum_values(self):
        assert ChannelType.PUBLIC.value == "public"
        assert ChannelType.PRIVATE.value == "private"

    def test_channel_id_is_uuid(self):
        channel = Channel(
            id=uuid.uuid4(),
            name="uuid-channel",
            creator_id=uuid.uuid4(),
        )
        assert isinstance(channel.id, uuid.UUID)
        assert isinstance(channel.creator_id, uuid.UUID)
