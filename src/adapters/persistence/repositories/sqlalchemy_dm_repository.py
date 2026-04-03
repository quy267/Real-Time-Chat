"""SQLAlchemy implementation of DirectMessageRepository."""

import uuid as _uuid_module
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.direct_conversation_model import (
    DirectConversationMemberModel,
    DirectConversationModel,
)
from src.domain.entities.direct_conversation import DirectConversation
from src.domain.repositories.dm_repository import DirectMessageRepository


class SQLAlchemyDmRepository(DirectMessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_conversation(self, user_ids: list[UUID]) -> DirectConversation:
        model = DirectConversationModel(id=_uuid_module.uuid4())
        self._session.add(model)
        await self._session.flush()
        for uid in user_ids:
            member = DirectConversationMemberModel(
                conversation_id=model.id, user_id=uid
            )
            self._session.add(member)
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def get_conversation(self, conversation_id: UUID) -> DirectConversation | None:
        result = await self._session.execute(
            select(DirectConversationModel).where(DirectConversationModel.id == conversation_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_conversation_by_participants(
        self, user_id_1: UUID, user_id_2: UUID
    ) -> DirectConversation | None:
        # Find conversations where both users are members
        subq1 = select(DirectConversationMemberModel.conversation_id).where(
            DirectConversationMemberModel.user_id == user_id_1
        )
        subq2 = select(DirectConversationMemberModel.conversation_id).where(
            DirectConversationMemberModel.user_id == user_id_2
        )
        result = await self._session.execute(
            select(DirectConversationModel).where(
                DirectConversationModel.id.in_(subq1),
                DirectConversationModel.id.in_(subq2),
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_conversations(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[DirectConversation]:
        subq = select(DirectConversationMemberModel.conversation_id).where(
            DirectConversationMemberModel.user_id == user_id
        )
        result = await self._session.execute(
            select(DirectConversationModel)
            .where(DirectConversationModel.id.in_(subq))
            .order_by(DirectConversationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [row.to_entity() for row in result.scalars().all()]

    async def add_member(self, conversation_id: UUID, user_id: UUID) -> None:
        member = DirectConversationMemberModel(
            conversation_id=conversation_id, user_id=user_id
        )
        self._session.add(member)
        await self._session.flush()
        await self._session.commit()

    async def is_participant(self, conversation_id: UUID, user_id: UUID) -> bool:
        result = await self._session.execute(
            select(DirectConversationMemberModel).where(
                DirectConversationMemberModel.conversation_id == conversation_id,
                DirectConversationMemberModel.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None
