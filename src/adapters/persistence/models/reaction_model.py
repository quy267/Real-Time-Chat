"""SQLAlchemy ORM model for the `reactions` table."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base, UUIDPrimaryKeyMixin
from src.domain.entities.reaction import Reaction


class ReactionModel(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reactions"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", "emoji", name="uq_reactions_message_user_emoji"),
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    emoji: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_entity(self) -> Reaction:
        return Reaction(
            id=self.id,
            message_id=self.message_id,
            user_id=self.user_id,
            emoji=self.emoji,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: Reaction) -> "ReactionModel":
        return cls(
            id=entity.id,
            message_id=entity.message_id,
            user_id=entity.user_id,
            emoji=entity.emoji,
            created_at=entity.created_at,
        )
