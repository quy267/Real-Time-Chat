"""SQLAlchemy implementation of MentionRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.mention_model import MentionModel
from src.domain.entities.mention import Mention
from src.domain.repositories.mention_repository import MentionRepository


class SQLAlchemyMentionRepository(MentionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, mention: Mention) -> Mention:
        model = MentionModel.from_entity(mention)
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Mention]:
        result = await self._session.execute(
            select(MentionModel)
            .where(MentionModel.mentioned_user_id == user_id)
            .order_by(MentionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [row.to_entity() for row in result.scalars().all()]
