"""GetUnreadCountUseCase — return unread message count for a user in a channel."""

from uuid import UUID

from src.adapters.redis.read_receipt_store import ReadReceiptStore
from src.domain.repositories.message_repository import MessageRepository


class GetUnreadCountUseCase:
    def __init__(
        self,
        read_receipt_store: ReadReceiptStore,
        message_repo: MessageRepository,
    ) -> None:
        self._store = read_receipt_store
        self._message_repo = message_repo

    async def execute(self, user_id: str, channel_id: str) -> int:
        """Return number of messages newer than the user's last-read position."""
        last_read_id = await self._store.get_last_read(user_id, channel_id)

        channel_uuid = UUID(channel_id)
        if last_read_id is None:
            # No read receipt — all messages are unread; use COUNT(*) not full fetch
            return await self._message_repo.count_by_channel(channel_uuid)

        pivot = await self._message_repo.get_by_id(UUID(last_read_id))
        if pivot is None:
            return 0

        # Count messages newer than the pivot using get_by_channel with before=None.
        # For large channels this still fetches rows; a future optimisation is to
        # add count_after_timestamp to the repo. Acceptable trade-off for now.
        unread = await self._message_repo.get_by_channel(
            channel_id=channel_uuid, limit=1000, before=None
        )
        return sum(1 for m in unread if m.created_at > pivot.created_at)
