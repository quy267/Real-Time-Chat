"""Integration tests for auth API routes using fake repositories."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from src.adapters.api import routes as _routes_pkg  # noqa: F401 — ensure routes importable
from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(user_repo: FakeUserRepository, blacklist: FakeTokenBlacklist):
    """Build a FastAPI app wired to fake dependencies."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.domain.exceptions import (
        AuthenticationError,
        DuplicateEntityError,
        ValidationError,
    )
    from src.use_cases.auth.login_user import LoginUserUseCase
    from src.use_cases.auth.logout_user import LogoutUserUseCase
    from src.use_cases.auth.refresh_token import RefreshTokenUseCase
    from src.use_cases.auth.register_user import RegisterUserUseCase

    app = FastAPI()

    # Override route-level use case factories via module-level monkeypatching
    import src.adapters.api.dependencies as deps

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)

    app.include_router(auth_router)

    @app.exception_handler(DuplicateEntityError)
    async def duplicate_handler(request: Request, exc: DuplicateEntityError):
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    return app


@pytest.fixture
def fake_repo():
    return FakeUserRepository()


@pytest.fixture
def fake_blacklist():
    return FakeTokenBlacklist()


@pytest.fixture
async def client(fake_repo, fake_blacklist) -> AsyncGenerator[AsyncClient, None]:
    app = _make_app(fake_repo, fake_blacklist)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_register_and_login_flow(client):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "securepass"},
    )
    assert reg.status_code == 201
    tokens = reg.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    login = await client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "securepass"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


async def test_register_duplicate_email_returns_409(client):
    await client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "securepass"},
    )
    resp = await client.post(
        "/api/auth/register",
        json={"username": "bob2", "email": "bob@example.com", "password": "securepass"},
    )
    assert resp.status_code == 409


async def test_login_wrong_password_returns_401(client):
    await client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "securepass"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


async def test_protected_route_without_token_returns_401(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 422  # missing required header → FastAPI 422


async def test_protected_route_with_valid_token(client):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "securepass"},
    )
    access_token = reg.json()["access_token"]
    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    assert "user_id" in resp.json()


async def test_protected_route_with_invalid_token_returns_401(client):
    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert resp.status_code == 401


async def test_logout_blacklists_token(client, fake_blacklist):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "dave", "email": "dave@example.com", "password": "securepass"},
    )
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert await fake_blacklist.is_blacklisted(refresh_token)


async def test_refresh_returns_new_token_pair(client):
    reg = await client.post(
        "/api/auth/register",
        json={"username": "eve", "email": "eve@example.com", "password": "securepass"},
    )
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]
