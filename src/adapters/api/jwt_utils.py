"""JWT encode/decode utilities — access and refresh tokens."""

from datetime import datetime, timedelta, timezone

import jwt

from src.domain.value_objects.token_pair import TokenPair
from src.infrastructure.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str) -> str:
    """Encode a short-lived access JWT (15 min)."""
    now = _now()
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    """Encode a long-lived refresh JWT (7 days)."""
    now = _now()
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
        "iat": now,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def create_token_pair(user_id: str) -> TokenPair:
    """Convenience: create both access and refresh tokens."""
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )
