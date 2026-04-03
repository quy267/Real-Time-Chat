"""GetChannelUseCase — fetch channel by id, enforce membership for private channels."""

from uuid import UUID

from src.domain.entities.channel import Channel, ChannelType
from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.domain.repositories.channel_repository import ChannelRepository
from src.domain.repositories.membership_repository import MembershipRepository


class GetChannelUseCase:
    def __init__(
        self,
        channel_repo: ChannelRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._channel_repo = channel_repo
        self._membership_repo = membership_repo

    async def execute(self, channel_id: str, user_id: str) -> Channel:
        channel_uuid: UUID = UUID(channel_id)
        user_uuid: UUID = UUID(user_id)

        channel = await self._channel_repo.get_by_id(channel_uuid)
        if not channel:
            raise EntityNotFoundError(f"Channel '{channel_id}' not found.")

        if channel.channel_type == ChannelType.PRIVATE:
            is_member = await self._membership_repo.is_member(user_uuid, channel_uuid)
            if not is_member:
                raise AuthorizationError("You are not a member of this private channel.")

        return channel
