"""JoinChannelUseCase — add user to a public channel."""

from uuid import UUID

from src.domain.entities.channel import ChannelType
from src.domain.entities.membership import MemberRole, Membership
from src.domain.exceptions import AuthorizationError, DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.channel_repository import ChannelRepository
from src.domain.repositories.membership_repository import MembershipRepository


class JoinChannelUseCase:
    def __init__(
        self,
        channel_repo: ChannelRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self._channel_repo = channel_repo
        self._membership_repo = membership_repo

    async def execute(self, channel_id: str, user_id: str) -> Membership:
        channel_uuid: UUID = UUID(channel_id)
        user_uuid: UUID = UUID(user_id)

        channel = await self._channel_repo.get_by_id(channel_uuid)
        if not channel:
            raise EntityNotFoundError(f"Channel '{channel_id}' not found.")

        if channel.channel_type == ChannelType.PRIVATE:
            raise AuthorizationError("Cannot self-join a private channel.")

        already_member = await self._membership_repo.is_member(user_uuid, channel_uuid)
        if already_member:
            raise DuplicateEntityError("User is already a member of this channel.")

        return await self._membership_repo.add_member(user_uuid, channel_uuid, MemberRole.MEMBER)
