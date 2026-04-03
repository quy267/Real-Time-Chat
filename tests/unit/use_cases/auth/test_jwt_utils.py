"""Unit tests for JWT encode/decode utilities."""

from datetime import timedelta

import jwt
import pytest

from src.adapters.api.jwt_utils import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
)
from src.infrastructure.config import settings


def test_create_access_token_has_correct_type():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["type"] == "access"
    assert payload["sub"] == "user-123"


def test_create_refresh_token_has_correct_type():
    token = create_refresh_token("user-456")
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["sub"] == "user-456"


def test_decode_valid_token_returns_payload():
    token = create_access_token("user-789")
    payload = decode_token(token)
    assert payload["sub"] == "user-789"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_expired_token_raises():
    from datetime import datetime, timezone

    # Manually craft an already-expired token
    payload = {
        "sub": "user-999",
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        "iat": datetime.now(timezone.utc) - timedelta(minutes=16),
    }
    expired_token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired_token)


def test_decode_invalid_token_raises():
    with pytest.raises(jwt.PyJWTError):
        decode_token("not.a.valid.jwt")


def test_create_token_pair_returns_both_tokens():
    pair = create_token_pair("user-abc")
    assert pair.access_token
    assert pair.refresh_token
    access_payload = decode_token(pair.access_token)
    refresh_payload = decode_token(pair.refresh_token)
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    assert access_payload["sub"] == "user-abc"
