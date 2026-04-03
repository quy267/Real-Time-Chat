"""BcryptPasswordService — adapter implementation of PasswordService using password_utils."""

from src.adapters.api.password_utils import hash_password, verify_password
from src.domain.repositories.password_service import PasswordService


class BcryptPasswordService(PasswordService):
    """Wraps password_utils functions; injected into auth use cases via dependencies.py."""

    def hash_password(self, password: str) -> str:
        return hash_password(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return verify_password(plain, hashed)
