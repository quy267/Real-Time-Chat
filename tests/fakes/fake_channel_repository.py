"""In-memory ChannelRepository for unit tests — no database dependency."""

from uuid import UUID

from src.domain.entities.channel import Channel
from src.domain.repositories.channel_repository import ChannelRepository


class FakeChannelRepository(ChannelRepository):
    """Stores channels in a dict; keyed by channel.id.

    Membership filtering behaviour:
    - By default, list_by_user returns ALL channels (backward-compatible with
      tests that use a separate FakeMembershipRepository for membership logic).
    - Call register_membership(user_id, channel_id) to opt into proper per-user
      filtering for tests that need it.

    NOTE: Returns all channels by default — membership filtering is done in the
    use case or SQL repo in production. Use register_membership() for tests that
    need accurate authorization filtering.
    """

    def __init__(self) -> None:
        self._store: dict[UUID, Channel] = {}
        # user_id -> set of channel_ids the user belongs to.
        # Empty means "not configured" → fall back to returning all channels.
        self._user_channels: dict[UUID, set[UUID]] = {}

    def register_membership(self, user_id: UUID, channel_id: UUID) -> None:
        """Register a user as a member of a channel (for test setup).

        Once called for a user, list_by_user will filter to only that user's channels.
        """
        self._user_channels.setdefault(user_id, set()).add(channel_id)

    async def create(self, channel: Channel) -> Channel:
        self._store[channel.id] = channel
        return channel

    async def get_by_id(self, channel_id: UUID) -> Channel | None:
        return self._store.get(channel_id)

    async def get_by_name(self, name: str) -> Channel | None:
        for channel in self._store.values():
            if channel.name == name:
                return channel
        return None

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Channel]:
        if user_id in self._user_channels:
            # Membership-aware mode: return only channels the user is registered in
            cids = self._user_channels[user_id]
            channels = [c for c in self._store.values() if c.id in cids]
        else:
            # Fallback mode: return all channels (backward-compatible default)
            channels = list(self._store.values())
        return channels[offset : offset + limit]

    async def update(self, channel: Channel) -> Channel:
        self._store[channel.id] = channel
        return channel

    async def delete(self, channel_id: UUID) -> None:
        self._store.pop(channel_id, None)
