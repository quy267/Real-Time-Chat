"""SQLAlchemy implementation of ReactionRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.reaction_model import ReactionModel
from src.domain.entities.reaction import Reaction
from src.domain.repositories.reaction_repository import ReactionRepository


class SQLAlchemyReactionRepository(ReactionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, reaction: Reaction) -> Reaction:
        model = ReactionModel.from_entity(reaction)
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def remove(self, message_id: UUID, user_id: UUID, emoji: str) -> None:
        result = await self._session.execute(
            select(ReactionModel).where(
                ReactionModel.message_id == message_id,
                ReactionModel.user_id == user_id,
                ReactionModel.emoji == emoji,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            await self._session.commit()

    async def list_by_message(self, message_id: UUID) -> list[Reaction]:
        result = await self._session.execute(
            select(ReactionModel)
            .where(ReactionModel.message_id == message_id)
            .order_by(ReactionModel.created_at)
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def get(self, message_id: UUID, user_id: UUID, emoji: str) -> Reaction | None:
        result = await self._session.execute(
            select(ReactionModel).where(
                ReactionModel.message_id == message_id,
                ReactionModel.user_id == user_id,
                ReactionModel.emoji == emoji,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
