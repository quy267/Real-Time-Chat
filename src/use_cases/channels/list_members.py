"""ListMembersUseCase — return paginated members for a channel."""

from uuid import UUID

from src.domain.entities.membership import Membership
from src.domain.exceptions import AuthorizationError, EntityNotFoundError
from src.domain.repositories.channel_repository import ChannelRepository
from src.domain.repositories.membership_repository import MembershipRepository


class ListMembersUseCase:
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
        limit: int = 50,
        offset: int = 0,
    ) -> list[Membership]:
        channel_uuid: UUID = UUID(channel_id)
        user_uuid: UUID = UUID(user_id)

        channel = await self._channel_repo.get_by_id(channel_uuid)
        if not channel:
            raise EntityNotFoundError(f"Channel '{channel_id}' not found.")

        is_member = await self._membership_repo.is_member(user_uuid, channel_uuid)
        if not is_member:
            raise AuthorizationError("You must be a member to view channel members.")

        return await self._membership_repo.list_members(channel_uuid, limit=limit, offset=offset)
