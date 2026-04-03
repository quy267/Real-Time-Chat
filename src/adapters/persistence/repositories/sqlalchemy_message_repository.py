"""SQLAlchemy implementation of MessageRepository with cursor-based pagination."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.message_model import MessageModel
from src.domain.entities.message import Message
from src.domain.exceptions import EntityNotFoundError
from src.domain.repositories.message_repository import MessageRepository


class SQLAlchemyMessageRepository(MessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, message: Message) -> Message:
        model = MessageModel.from_entity(message)
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def get_by_id(self, message_id: UUID) -> Message | None:
        result = await self._session.execute(
            select(MessageModel).where(MessageModel.id == message_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_channel(
        self,
        channel_id: UUID,
        limit: int = 50,
        before: datetime | None = None,
    ) -> list[Message]:
        query = (
            select(MessageModel)
            .where(MessageModel.channel_id == channel_id)
            .order_by(MessageModel.created_at.desc())
            .limit(limit)
        )
        if before is not None:
            query = query.where(MessageModel.created_at < before)
        result = await self._session.execute(query)
        return [row.to_entity() for row in result.scalars().all()]

    async def count_by_channel(self, channel_id: UUID) -> int:
        """Return total message count using SELECT COUNT(*)."""
        result = await self._session.execute(
            select(func.count()).where(MessageModel.channel_id == channel_id)
        )
        return result.scalar_one()

    async def search_by_content(
        self,
        query: str,
        channel_ids: list[UUID],
        limit: int = 20,
    ) -> list[Message]:
        """Case-insensitive content search across multiple channels using ILIKE."""
        if not channel_ids:
            return []
        result = await self._session.execute(
            select(MessageModel)
            .where(
                MessageModel.channel_id.in_(channel_ids),
                MessageModel.content.ilike(f"%{query}%"),
            )
            .order_by(MessageModel.created_at.desc())
            .limit(limit)
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def update(self, message: Message) -> Message:
        result = await self._session.execute(
            select(MessageModel).where(MessageModel.id == message.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise EntityNotFoundError(f"Message '{message.id}' not found.")
        model.content = message.content
        model.file_url = message.file_url
        model.updated_at = message.updated_at
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def delete(self, message_id: UUID) -> None:
        result = await self._session.execute(
            select(MessageModel).where(MessageModel.id == message_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise EntityNotFoundError(f"Message '{message_id}' not found.")
        await self._session.delete(model)
        await self._session.flush()
        await self._session.commit()
