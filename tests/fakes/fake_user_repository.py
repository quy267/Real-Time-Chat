"""In-memory UserRepository for unit tests — no database dependency."""

from uuid import UUID

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    """Stores users in a dict; keyed by user.id."""

    def __init__(self) -> None:
        self._store: dict[UUID, User] = {}

    async def create(self, user: User) -> User:
        self._store[user.id] = user
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._store.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        for user in self._store.values():
            if user.email == email:
                return user
        return None

    async def get_by_username(self, username: str) -> User | None:
        for user in self._store.values():
            if user.username == username:
                return user
        return None

    async def update(self, user: User) -> User:
        self._store[user.id] = user
        return user

    async def delete(self, user_id: UUID) -> None:
        self._store.pop(user_id, None)
