"""LeaveChannelUseCase — remove user from channel; creator cannot leave."""

from uuid import UUID

from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.domain.repositories.channel_repository import ChannelRepository
from src.domain.repositories.membership_repository import MembershipRepository


class LeaveChannelUseCase:
    def __init__(
        self,
        channel_repo: ChannelRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._channel_repo = channel_repo
        self._membership_repo = membership_repo

    async def execute(self, channel_id: str, user_id: str) -> None:
        channel_uuid: UUID = UUID(channel_id)
        user_uuid: UUID = UUID(user_id)

        channel = await self._channel_repo.get_by_id(channel_uuid)
        if not channel:
            raise EntityNotFoundError(f"Channel '{channel_id}' not found.")

        if channel.creator_id == user_uuid:
            raise AuthorizationError(
                "Channel creator cannot leave their own channel. Delete it instead."
            )

        await self._membership_repo.remove_member(user_uuid, channel_uuid)
