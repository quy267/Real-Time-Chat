"""CreateChannelUseCase — validate, create channel, auto-add creator as admin."""

import uuid
from uuid import UUID

from src.domain.entities.channel import Channel, ChannelType
from src.domain.entities.membership import MemberRole
from src.domain.exceptions import DuplicateEntityError, ValidationError
from src.domain.repositories.channel_repository import ChannelRepository
from src.domain.repositories.membership_repository import MembershipRepository

_VALID_TYPES = {t.value for t in ChannelType}


class CreateChannelUseCase:
    def __init__(
        self,
        channel_repo: ChannelRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._channel_repo = channel_repo
        self._membership_repo = membership_repo

    async def execute(
        self,
        name: str,
        description: str,
        channel_type: str,
        creator_id: str,
    ) -> Channel:
        name = name.strip()
        if not name:
            raise ValidationError("Channel name must not be empty.")
        if channel_type not in _VALID_TYPES:
            raise ValidationError(f"Invalid channel type '{channel_type}'.")

        existing = await self._channel_repo.get_by_name(name)
        if existing:
            raise DuplicateEntityError(f"Channel name '{name}' is already taken.")

        creator_uuid: UUID = UUID(creator_id)
        channel = Channel(
            id=uuid.uuid4(),
            name=name,
            description=description or None,
            channel_type=ChannelType(channel_type),
            creator_id=creator_uuid,
        )
        channel = await self._channel_repo.create(channel)
        await self._membership_repo.add_member(creator_uuid, channel.id, MemberRole.ADMIN)
        return channel
