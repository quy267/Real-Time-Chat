"""In-memory token blacklist for unit tests — no Redis dependency."""


class FakeTokenBlacklist:
    """Stores blacklisted tokens in a set."""

    def __init__(self) -> None:
        self._blacklisted: set[str] = set()

    async def blacklist(self, token: str, expires_in_seconds: int) -> None:  # noqa: ARG002
        self._blacklisted.add(token)

    async def is_blacklisted(self, token: str) -> bool:
        return token in self._blacklisted
