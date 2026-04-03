"""SQLAlchemy implementation of ChannelRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.channel_model import ChannelModel
from src.adapters.persistence.models.membership_model import MembershipModel
from src.domain.entities.channel import Channel
from src.domain.exceptions import EntityNotFoundError
from src.domain.repositories.channel_repository import ChannelRepository


class SQLAlchemyChannelRepository(ChannelRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, channel: Channel) -> Channel:
        model = ChannelModel.from_entity(channel)
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def get_by_id(self, channel_id: UUID) -> Channel | None:
        result = await self._session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_name(self, name: str) -> Channel | None:
        result = await self._session.execute(
            select(ChannelModel).where(ChannelModel.name == name)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Channel]:
        result = await self._session.execute(
            select(ChannelModel)
            .join(MembershipModel, MembershipModel.channel_id == ChannelModel.id)
            .where(MembershipModel.user_id == user_id)
            .limit(limit)
            .offset(offset)
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def update(self, channel: Channel) -> Channel:
        result = await self._session.execute(
            select(ChannelModel).where(ChannelModel.id == channel.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise EntityNotFoundError(f"Channel '{channel.id}' not found.")
        model.name = channel.name
        model.description = channel.description
        model.channel_type = channel.channel_type.value
        model.updated_at = channel.updated_at
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def delete(self, channel_id: UUID) -> None:
        result = await self._session.execute(
            select(ChannelModel).where(ChannelModel.id == channel_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise EntityNotFoundError(f"Channel '{channel_id}' not found.")
        await self._session.delete(model)
        await self._session.flush()
        await self._session.commit()
