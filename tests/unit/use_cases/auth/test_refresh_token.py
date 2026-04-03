"""Unit tests for RefreshTokenUseCase."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.adapters.api.jwt_token_service import JwtTokenService
from src.adapters.api.jwt_utils import create_refresh_token
from src.domain.exceptions import AuthenticationError
from src.infrastructure.config import settings
from src.use_cases.auth.refresh_token import RefreshTokenUseCase
from tests.fakes.fake_token_blacklist import FakeTokenBlacklist

_token_svc = JwtTokenService()


@pytest.fixture
def blacklist():
    return FakeTokenBlacklist()


@pytest.fixture
def use_case(blacklist):
    return RefreshTokenUseCase(blacklist, _token_svc)


async def test_refresh_success(use_case, blacklist):
    refresh_token = create_refresh_token("user-123")
    pair = await use_case.execute(refresh_token)
    assert pair.access_token
    assert pair.refresh_token
    # Old token should be blacklisted after rotation
    assert await blacklist.is_blacklisted(refresh_token)


async def test_refresh_blacklisted_token(use_case, blacklist):
    refresh_token = create_refresh_token("user-123")
    await blacklist.blacklist(refresh_token, expires_in_seconds=3600)
    with pytest.raises(AuthenticationError):
        await use_case.execute(refresh_token)


async def test_refresh_expired_token(use_case):
    payload = {
        "sub": "user-123",
        "type": "refresh",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        "iat": datetime.now(timezone.utc) - timedelta(days=8),
    }
    expired = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(AuthenticationError):
        await use_case.execute(expired)


async def test_refresh_with_access_token_raises(use_case):
    """Passing an access token where refresh is expected should be rejected."""
    from src.adapters.api.jwt_utils import create_access_token

    access_token = create_access_token("user-123")
    with pytest.raises(AuthenticationError):
        await use_case.execute(access_token)
