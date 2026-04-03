"""SQLAlchemy implementation of UserRepository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.models.user_model import UserModel
from src.domain.entities.user import User
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError
from src.domain.repositories.user_repository import UserRepository


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        existing = await self._session.execute(
            select(UserModel).where(UserModel.email == user.email)
        )
        if existing.scalar_one_or_none():
            raise DuplicateEntityError(f"User with email '{user.email}' already exists.")
        model = UserModel.from_entity(user)
        self._session.add(model)
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def update(self, user: User) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise EntityNotFoundError(f"User '{user.id}' not found.")
        model.username = user.username
        model.email = user.email
        model.password_hash = user.password_hash
        model.display_name = user.display_name
        model.avatar_url = user.avatar_url
        model.status = user.status.value
        model.updated_at = user.updated_at
        await self._session.flush()
        await self._session.commit()
        return model.to_entity()

    async def delete(self, user_id: UUID) -> None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise EntityNotFoundError(f"User '{user_id}' not found.")
        await self._session.delete(model)
        await self._session.flush()
        await self._session.commit()
