"""SQLAlchemy implementation of MembershipRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.membership_model import MembershipModel
from src.domain.entities.membership import MemberRole, Membership
from src.domain.repositories.membership_repository import MembershipRepository


class SQLAlchemyMembershipRepository(MembershipRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_member(self, user_id: UUID, channel_id: UUID, role: MemberRole) -> Membership:
        model = MembershipModel(
            user_id=user_id,
            channel_id=channel_id,
            role=role.value,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        # Re-fetch to get server-generated joined_at
        result = await self._session.execute(
            select(MembershipModel).where(
                MembershipModel.user_id == user_id,
                MembershipModel.channel_id == channel_id,
            )
        )
        return result.scalar_one().to_entity()

    async def remove_member(self, user_id: UUID, channel_id: UUID) -> None:
        result = await self._session.execute(
            select(MembershipModel).where(
                MembershipModel.user_id == user_id,
                MembershipModel.channel_id == channel_id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
            await self._session.commit()

    async def get_member(self, user_id: UUID, channel_id: UUID) -> Membership | None:
        result = await self._session.execute(
            select(MembershipModel).where(
                MembershipModel.user_id == user_id,
                MembershipModel.channel_id == channel_id,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_members(
        self, channel_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Membership]:
        result = await self._session.execute(
            select(MembershipModel)
            .where(MembershipModel.channel_id == channel_id)
            .offset(offset)
            .limit(limit)
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def is_member(self, user_id: UUID, channel_id: UUID) -> bool:
        result = await self._session.execute(
            select(MembershipModel).where(
                MembershipModel.user_id == user_id,
                MembershipModel.channel_id == channel_id,
            )
        )
        return result.scalar_one_or_none() is not None
