"""UpdateChannelUseCase — update name/description, restricted to admin/creator."""

from datetime import datetime, timezone
from uuid import UUID

from src.domain.entities.channel import Channel
from src.domain.entities.membership import MemberRole
from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.domain.repositories.channel_repository import ChannelRepository
from src.domain.repositories.membership_repository import MembershipRepository


class UpdateChannelUseCase:
    def __init__(
        self,
        channel_repo: ChannelRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._channel_repo = channel_repo
        self._membership_repo = membership_repo

    async def execute(
        self,
        channel_id: str,
        user_id: str,
        name: str | None,
        description: str | None,
    ) -> Channel:
        channel_uuid: UUID = UUID(channel_id)
        user_uuid: UUID = UUID(user_id)

        channel = await self._channel_repo.get_by_id(channel_uuid)
        if not channel:
            raise EntityNotFoundError(f"Channel '{channel_id}' not found.")

        membership = await self._membership_repo.get_member(user_uuid, channel_uuid)
        if not membership or membership.role not in (MemberRole.ADMIN,):
            raise AuthorizationError("Only channel admins can update channel details.")

        if name is not None:
            channel.name = name.strip() or channel.name
        if description is not None:
            channel.description = description
        channel.updated_at = datetime.now(timezone.utc)

        return await self._channel_repo.update(channel)
