"""JwtTokenService — adapter implementation of TokenService using jwt_utils."""

from src.adapters.api.jwt_utils import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
)
from src.domain.repositories.token_service import TokenService
from src.domain.value_objects.token_pair import TokenPair


class JwtTokenService(TokenService):
    """Wraps jwt_utils functions; injected into auth use cases via dependencies.py."""

    def create_token_pair(self, user_id: str) -> TokenPair:
        return create_token_pair(user_id)

    def decode_token(self, token: str) -> dict:
        return decode_token(token)

    def create_access_token(self, user_id: str) -> str:
        return create_access_token(user_id)

    def create_refresh_token(self, user_id: str) -> str:
        return create_refresh_token(user_id)
