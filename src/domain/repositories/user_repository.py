"""Abstract UserRepository — async interface for user persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        """Persist a new user and return it."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Return user by primary key, or None if not found."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Return user by email address, or None if not found."""

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Return user by username, or None if not found."""

    @abstractmethod
    async def update(self, user: User) -> User:
        """Persist changes to an existing user and return updated entity."""

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """Remove a user by primary key."""
