"""Unit tests for RegisterUserUseCase."""

import pytest

from src.adapters.api.bcrypt_password_service import BcryptPasswordService
from src.adapters.api.jwt_token_service import JwtTokenService
from src.domain.exceptions import DuplicateEntityError, ValidationError
from src.use_cases.auth.register_user import RegisterUserUseCase
from tests.fakes.fake_user_repository import FakeUserRepository


@pytest.fixture
def repo():
    return FakeUserRepository()


@pytest.fixture
def use_case(repo):
    return RegisterUserUseCase(repo, BcryptPasswordService(), JwtTokenService())


async def test_register_success(use_case):
    pair = await use_case.execute("alice", "alice@example.com", "password123")
    assert pair.access_token
    assert pair.refresh_token


async def test_register_duplicate_email(use_case):
    await use_case.execute("alice", "alice@example.com", "password123")
    with pytest.raises(DuplicateEntityError):
        await use_case.execute("alice2", "alice@example.com", "password456")


async def test_register_duplicate_username(use_case):
    await use_case.execute("alice", "alice@example.com", "password123")
    with pytest.raises(DuplicateEntityError):
        await use_case.execute("alice", "other@example.com", "password456")


async def test_register_weak_password(use_case):
    with pytest.raises(ValidationError):
        await use_case.execute("alice", "alice@example.com", "short")


async def test_register_invalid_email_format(use_case):
    with pytest.raises(ValidationError):
        await use_case.execute("alice", "not-an-email", "password123")


async def test_register_short_username(use_case):
    with pytest.raises(ValidationError):
        await use_case.execute("ab", "alice@example.com", "password123")
