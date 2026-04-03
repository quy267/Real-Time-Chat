"""Abstract ChannelRepository — async interface for channel persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.channel import Channel


class ChannelRepository(ABC):
    @abstractmethod
    async def create(self, channel: Channel) -> Channel:
        """Persist a new channel and return it."""

    @abstractmethod
    async def get_by_id(self, channel_id: UUID) -> Channel | None:
        """Return channel by primary key, or None if not found."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Channel | None:
        """Return channel by name, or None if not found."""

    @abstractmethod
    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Channel]:
        """Return paginated channels the user is a member of."""

    @abstractmethod
    async def update(self, channel: Channel) -> Channel:
        """Persist changes to an existing channel and return updated entity."""

    @abstractmethod
    async def delete(self, channel_id: UUID) -> None:
        """Remove a channel by primary key."""
