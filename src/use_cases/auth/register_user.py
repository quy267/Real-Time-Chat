"""RegisterUser use case — validate input, create user, return token pair."""

import re
import uuid

from src.domain.entities.user import User
from src.domain.exceptions import DuplicateEntityError, ValidationError
from src.domain.repositories.password_service import PasswordService
from src.domain.repositories.token_service import TokenService
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.token_pair import TokenPair

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ) -> None:
        self._user_repo = user_repo
        self._password_service = password_service
        self._token_service = token_service

    async def execute(self, username: str, email: str, password: str) -> TokenPair:
        """Register a new user and return a JWT token pair."""
        self._validate(username, email, password)

        if await self._user_repo.get_by_email(email):
            raise DuplicateEntityError("Email already registered")
        if await self._user_repo.get_by_username(username):
            raise DuplicateEntityError("Username already taken")

        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password_hash=self._password_service.hash_password(password),
        )
        await self._user_repo.create(user)
        return self._token_service.create_token_pair(str(user.id))

    @staticmethod
    def _validate(username: str, email: str, password: str) -> None:
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")
        if not _EMAIL_RE.match(email):
            raise ValidationError("Invalid email format")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
