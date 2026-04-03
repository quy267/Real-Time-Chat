"""SQLAlchemy implementation of ThreadRepository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.message_model import MessageModel
from src.adapters.persistence.models.thread_model import ThreadModel
from src.domain.entities.message import Message
from src.domain.entities.thread import Thread
from src.domain.repositories.thread_repository import ThreadRepository


class SQLAlchemyThreadRepository(ThreadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, thread: Thread) -> Thread:
        model = ThreadModel.from_entity(thread)
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def get_by_id(self, thread_id: UUID) -> Thread | None:
        result = await self._session.execute(
            select(ThreadModel).where(ThreadModel.id == thread_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_parent_message_id(self, parent_message_id: UUID) -> Thread | None:
        result = await self._session.execute(
            select(ThreadModel).where(ThreadModel.parent_message_id == parent_message_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_replies(
        self,
        thread_id: UUID,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Message]:
        query = (
            select(MessageModel)
            .where(MessageModel.thread_id == thread_id)
            .order_by(MessageModel.created_at.desc())
            .limit(limit)
        )
        if before is not None:
            query = query.where(MessageModel.created_at < before)
        result = await self._session.execute(query)
        return [row.to_entity() for row in result.scalars().all()]
