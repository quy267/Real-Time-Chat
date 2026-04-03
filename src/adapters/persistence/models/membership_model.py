"""SQLAlchemy ORM model for the `memberships` table (composite PK)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base
from src.domain.entities.membership import MemberRole, Membership


class MembershipModel(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        Index("ix_memberships_user_id", "user_id"),
        Index("ix_memberships_channel_id", "channel_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default=MemberRole.MEMBER.value
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_entity(self) -> Membership:
        return Membership(
            user_id=self.user_id,
            channel_id=self.channel_id,
            role=MemberRole(self.role),
            joined_at=self.joined_at,
        )

    @classmethod
    def from_entity(cls, entity: Membership) -> "MembershipModel":
        return cls(
            user_id=entity.user_id,
            channel_id=entity.channel_id,
            role=entity.role.value,
            joined_at=entity.joined_at,
        )
