"""RemoveReactionUseCase — remove an emoji reaction from a message."""

from uuid import UUID

from src.domain.exceptions import EntityNotFoundError
from src.domain.repositories.reaction_repository import ReactionRepository


class RemoveReactionUseCase:
    def __init__(self, reaction_repo: ReactionRepository) -> None:
        self._reaction_repo = reaction_repo

    async def execute(
        self,
        message_id: str,
        user_id: str,
        emoji: str,
    ) -> None:
        """Remove reaction; raises EntityNotFoundError if it does not exist."""
        message_uuid = UUID(message_id)
        user_uuid = UUID(user_id)

        existing = await self._reaction_repo.get(message_uuid, user_uuid, emoji)
        if existing is None:
            raise EntityNotFoundError("Reaction not found.")

        await self._reaction_repo.remove(message_uuid, user_uuid, emoji)
