"""SQLAlchemy implementation of NotificationRepository."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.notification_model import NotificationModel
from src.domain.entities.notification import Notification
from src.domain.repositories.notification_repository import NotificationRepository


class SQLAlchemyNotificationRepository(NotificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, notification: Notification) -> Notification:
        model = NotificationModel.from_entity(notification)
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        result = await self._session.execute(
            select(NotificationModel).where(NotificationModel.id == notification_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        query = (
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if unread_only:
            query = query.where(NotificationModel.read.is_(False))
        result = await self._session.execute(query)
        return [row.to_entity() for row in result.scalars().all()]

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None:
        await self._session.execute(
            update(NotificationModel)
            .where(
                NotificationModel.id == notification_id,
                NotificationModel.user_id == user_id,
            )
            .values(read=True)
        )
        await self._session.flush()
        await self._session.commit()

    async def mark_all_read(self, user_id: UUID) -> None:
        await self._session.execute(
            update(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .values(read=True)
        )
        await self._session.flush()
        await self._session.commit()

    async def count_unread(self, user_id: UUID) -> int:
        from sqlalchemy import func, select

        result = await self._session.execute(
            select(func.count()).where(
                NotificationModel.user_id == user_id,
                NotificationModel.read.is_(False),
            )
        )
        return result.scalar_one()
