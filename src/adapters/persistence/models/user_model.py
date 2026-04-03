"""SQLAlchemy ORM model for the `users` table."""


from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.models.base_model import Base, TimestampMixin, UUIDPrimaryKeyMixin
from src.domain.entities.user import User
from src.domain.value_objects.presence_status import PresenceStatus


class UserModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PresenceStatus.OFFLINE.value
    )

    def to_entity(self) -> User:
        return User(
            id=self.id,
            username=self.username,
            email=self.email,
            password_hash=self.password_hash,
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            status=PresenceStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: User) -> "UserModel":
        return cls(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            password_hash=entity.password_hash,
            display_name=entity.display_name,
            avatar_url=entity.avatar_url,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
