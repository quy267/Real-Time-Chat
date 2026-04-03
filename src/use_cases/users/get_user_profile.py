"""GetUserProfileUseCase — retrieve a user's public profile."""

from uuid import UUID

from src.domain.entities.user import User
from src.domain.exceptions import EntityNotFoundError
from src.domain.repositories.user_repository import UserRepository


class GetUserProfileUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, user_id: str) -> User:
        """Return user entity; raises EntityNotFoundError if not found."""
        user = await self._user_repo.get_by_id(UUID(user_id))
        if user is None:
            raise EntityNotFoundError(f"User '{user_id}' not found.")
        return user
