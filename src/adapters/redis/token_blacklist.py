"""Redis-backed token blacklist — stores revoked JWTs with TTL."""

import redis.asyncio as aioredis


class TokenBlacklist:
    """Stores blacklisted JWT strings in Redis as keys with TTL."""

    _PREFIX = "blacklist:"

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    async def blacklist(self, token: str, expires_in_seconds: int) -> None:
        """Add token to blacklist with the given TTL (seconds)."""
        key = self._PREFIX + token
        await self._redis.set(key, "1", ex=expires_in_seconds)

    async def is_blacklisted(self, token: str) -> bool:
        """Return True if the token exists in the blacklist."""
        key = self._PREFIX + token
        return await self._redis.exists(key) > 0
