"""RefreshToken use case — rotate refresh token, return new pair."""

import jwt

from src.domain.exceptions import AuthenticationError
from src.domain.repositories.token_service import TokenService
from src.domain.value_objects.token_pair import TokenPair


class RefreshTokenUseCase:
    def __init__(self, token_blacklist, token_service: TokenService) -> None:
        self._blacklist = token_blacklist
        self._token_service = token_service

    async def execute(self, refresh_token: str) -> TokenPair:
        """Validate refresh token, blacklist it, and issue a new token pair."""
        try:
            payload = self._token_service.decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Refresh token has expired")
        except jwt.PyJWTError:
            raise AuthenticationError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Token is not a refresh token")

        if await self._blacklist.is_blacklisted(refresh_token):
            raise AuthenticationError("Refresh token has been revoked")

        user_id: str = payload["sub"]
        # Blacklist old token — TTL matches remaining token lifetime (7 days max)
        await self._blacklist.blacklist(refresh_token, expires_in_seconds=7 * 24 * 3600)
        return self._token_service.create_token_pair(user_id)
