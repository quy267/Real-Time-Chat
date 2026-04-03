"""SQLAlchemy ORM models for direct_conversations and junction table."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base, UUIDPrimaryKeyMixin
from src.domain.entities.direct_conversation import DirectConversation, DirectConversationMember


class DirectConversationModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "direct_conversations"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_entity(self) -> DirectConversation:
        return DirectConversation(
            id=self.id,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: DirectConversation) -> "DirectConversationModel":
        return cls(
            id=entity.id,
            created_at=entity.created_at,
        )


class DirectConversationMemberModel(Base):
    __tablename__ = "direct_conversation_members"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("direct_conversations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_entity(self) -> DirectConversationMember:
        return DirectConversationMember(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            joined_at=self.joined_at,
        )

    @classmethod
    def from_entity(cls, entity: DirectConversationMember) -> "DirectConversationMemberModel":
        return cls(
            conversation_id=entity.conversation_id,
            user_id=entity.user_id,
            joined_at=entity.joined_at,
        )
