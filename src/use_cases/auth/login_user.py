"""LoginUser use case — verify credentials, return token pair."""

from src.domain.exceptions import AuthenticationError
from src.domain.repositories.password_service import PasswordService
from src.domain.repositories.token_service import TokenService
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.token_pair import TokenPair


class LoginUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ) -> None:
        self._user_repo = user_repo
        self._password_service = password_service
        self._token_service = token_service

    async def execute(self, email: str, password: str) -> TokenPair:
        """Authenticate user by email/password and return a JWT token pair."""
        user = await self._user_repo.get_by_email(email)
        if user is None or not self._password_service.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        return self._token_service.create_token_pair(str(user.id))
