"""Unit tests for LoginUserUseCase."""

import uuid

import pytest

from src.adapters.api.bcrypt_password_service import BcryptPasswordService
from src.adapters.api.jwt_token_service import JwtTokenService
from src.adapters.api.password_utils import hash_password
from src.domain.entities.user import User
from src.domain.exceptions import AuthenticationError
from src.use_cases.auth.login_user import LoginUserUseCase
from tests.fakes.fake_user_repository import FakeUserRepository

_password_svc = BcryptPasswordService()
_token_svc = JwtTokenService()


@pytest.fixture
def repo():
    return FakeUserRepository()


@pytest.fixture
def use_case(repo):
    return LoginUserUseCase(repo, _password_svc, _token_svc)


async def test_login_success():
    repo = FakeUserRepository()
    user = User(
        id=uuid.uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=hash_password("password123"),
    )
    await repo.create(user)
    uc = LoginUserUseCase(repo, _password_svc, _token_svc)
    pair = await uc.execute("alice@example.com", "password123")
    assert pair.access_token
    assert pair.refresh_token


async def test_login_wrong_password():
    repo = FakeUserRepository()
    user = User(
        id=uuid.uuid4(),
        username="alice",
        email="alice@example.com",
        password_hash=hash_password("password123"),
    )
    await repo.create(user)
    uc = LoginUserUseCase(repo, _password_svc, _token_svc)
    with pytest.raises(AuthenticationError):
        await uc.execute("alice@example.com", "wrongpassword")


async def test_login_user_not_found(use_case):
    with pytest.raises(AuthenticationError):
        await use_case.execute("nobody@example.com", "password123")
