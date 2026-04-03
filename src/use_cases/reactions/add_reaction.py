"""AddReactionUseCase — add an emoji reaction to a message."""

import uuid
from uuid import UUID

from src.domain.entities.reaction import Reaction
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.message_repository import MessageRepository
from src.domain.repositories.reaction_repository import ReactionRepository


class AddReactionUseCase:
    def __init__(
        self,
        reaction_repo: ReactionRepository,
        message_repo: MessageRepository,
    ) -> None:
        self._reaction_repo = reaction_repo
        self._message_repo = message_repo

    async def execute(
        self,
        message_id: str,
        user_id: str,
        emoji: str,
    ) -> Reaction:
        """Add emoji reaction; raises EntityNotFoundError or DuplicateEntityError."""
        emoji = emoji.strip()
        if not emoji:
            from src.domain.exceptions import ValidationError
            raise ValidationError("Emoji must not be empty.")

        message_uuid = UUID(message_id)
        user_uuid = UUID(user_id)

        message = await self._message_repo.get_by_id(message_uuid)
        if message is None:
            raise EntityNotFoundError(f"Message '{message_id}' not found.")

        existing = await self._reaction_repo.get(message_uuid, user_uuid, emoji)
        if existing is not None:
            raise DuplicateEntityError("Reaction already exists.")

        reaction = Reaction(
            id=uuid.uuid4(),
            message_id=message_uuid,
            user_id=user_uuid,
            emoji=emoji,
        )
        return await self._reaction_repo.add(reaction)
