"""ListReactionsUseCase — list all reactions for a message with counts."""

from uuid import UUID

from src.domain.entities.reaction import Reaction
from src.domain.repositories.reaction_repository import ReactionRepository


class ListReactionsUseCase:
    def __init__(self, reaction_repo: ReactionRepository) -> None:
        self._reaction_repo = reaction_repo

    async def execute(self, message_id: str) -> list[Reaction]:
        """Return all reactions for the given message."""
        return await self._reaction_repo.list_by_message(UUID(message_id))
