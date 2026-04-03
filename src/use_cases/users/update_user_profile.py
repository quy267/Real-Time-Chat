"""UpdateUserProfileUseCase — update display_name, avatar_url, and status."""

from uuid import UUID

from src.domain.entities.user import User
from src.domain.exceptions import EntityNotFoundError, ValidationError
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.presence_status import PresenceStatus


class UpdateUserProfileUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(
        self,
        user_id: str,
        display_name: str | None = None,
        avatar_url: str | None = None,
        status: str | None = None,
    ) -> User:
        """Update allowed profile fields; returns updated User.

        Only non-None arguments are applied.
        Raises EntityNotFoundError if user does not exist.
        Raises ValidationError on invalid field values.
        """
        user = await self._user_repo.get_by_id(UUID(user_id))
        if user is None:
            raise EntityNotFoundError(f"User '{user_id}' not found.")

        if display_name is not None:
            display_name = display_name.strip()
            if len(display_name) > 64:
                raise ValidationError("Display name must not exceed 64 characters.")
            user.display_name = display_name or None

        if avatar_url is not None:
            avatar_url = avatar_url.strip()
            if avatar_url and not avatar_url.startswith(("http://", "https://", "/")):
                raise ValidationError("Avatar URL must be a valid URL or path.")
            user.avatar_url = avatar_url or None

        if status is not None:
            try:
                user.status = PresenceStatus(status)
            except ValueError:
                valid = [s.value for s in PresenceStatus]
                raise ValidationError(f"Invalid status. Must be one of: {valid}")

        return await self._user_repo.update(user)
