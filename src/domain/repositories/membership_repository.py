"""Abstract MembershipRepository — async interface for membership persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.membership import MemberRole, Membership


class MembershipRepository(ABC):
    @abstractmethod
    async def add_member(self, user_id: UUID, channel_id: UUID, role: MemberRole) -> Membership:
        """Add a user to a channel with the given role."""

    @abstractmethod
    async def remove_member(self, user_id: UUID, channel_id: UUID) -> None:
        """Remove a user from a channel."""

    @abstractmethod
    async def get_member(self, user_id: UUID, channel_id: UUID) -> Membership | None:
        """Return membership record, or None if not a member."""

    @abstractmethod
    async def list_members(
        self, channel_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Membership]:
        """Return paginated list of members for a channel."""

    @abstractmethod
    async def is_member(self, user_id: UUID, channel_id: UUID) -> bool:
        """Return True if user is a member of the channel."""
