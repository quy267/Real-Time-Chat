"""ListUserMentionsUseCase — fetch paginated mentions for the current user."""

from uuid import UUID

from src.domain.entities.mention import Mention
from src.domain.repositories.mention_repository import MentionRepository


class ListUserMentionsUseCase:
    def __init__(self, mention_repo: MentionRepository) -> None:
        self._mention_repo = mention_repo

    async def execute(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[Mention]:
        return await self._mention_repo.list_by_user(
            user_id=UUID(user_id),
            limit=limit,
            offset=offset,
        )
