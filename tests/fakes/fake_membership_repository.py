"""In-memory MembershipRepository for unit tests — no database dependency."""

from uuid import UUID

from src.domain.entities.membership import MemberRole, Membership
from src.domain.repositories.membership_repository import MembershipRepository


class FakeMembershipRepository(MembershipRepository):
    """Stores memberships in a dict keyed by (user_id, channel_id)."""

    def __init__(self) -> None:
        self._store: dict[tuple[UUID, UUID], Membership] = {}

    async def add_member(self, user_id: UUID, channel_id: UUID, role: MemberRole) -> Membership:
        membership = Membership(user_id=user_id, channel_id=channel_id, role=role)
        self._store[(user_id, channel_id)] = membership
        return membership

    async def remove_member(self, user_id: UUID, channel_id: UUID) -> None:
        self._store.pop((user_id, channel_id), None)

    async def get_member(self, user_id: UUID, channel_id: UUID) -> Membership | None:
        return self._store.get((user_id, channel_id))

    async def list_members(
        self, channel_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Membership]:
        members = [m for m in self._store.values() if m.channel_id == channel_id]
        return members[offset : offset + limit]

    async def is_member(self, user_id: UUID, channel_id: UUID) -> bool:
        return (user_id, channel_id) in self._store
