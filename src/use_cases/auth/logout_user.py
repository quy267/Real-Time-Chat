"""LogoutUser use case — blacklist refresh token in Redis."""


class LogoutUserUseCase:
    def __init__(self, token_blacklist) -> None:
        self._blacklist = token_blacklist

    async def execute(self, refresh_token: str) -> None:
        """Blacklist the refresh token so it cannot be reused."""
        await self._blacklist.blacklist(refresh_token, expires_in_seconds=7 * 24 * 3600)
