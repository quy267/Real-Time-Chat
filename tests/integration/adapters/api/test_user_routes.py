"""Integration tests for user profile API routes using fake repositories."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(user_repo, blacklist):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    import src.adapters.api.dependencies as deps
    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.user_routes import router as user_router
    from src.domain.exceptions import (
        AuthenticationError,
        EntityNotFoundError,
        ValidationError,
    )
    from src.use_cases.auth.login_user import LoginUserUseCase
    from src.use_cases.auth.logout_user import LogoutUserUseCase
    from src.use_cases.auth.refresh_token import RefreshTokenUseCase
    from src.use_cases.auth.register_user import RegisterUserUseCase
    from src.use_cases.users.get_user_profile import GetUserProfileUseCase
    from src.use_cases.users.update_user_profile import UpdateUserProfileUseCase

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)
    deps.get_user_profile_use_case = lambda: GetUserProfileUseCase(user_repo)
    deps.get_update_user_profile_use_case = lambda: UpdateUserProfileUseCase(user_repo)

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(user_router)

    @app.exception_handler(ValidationError)
    async def val_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(EntityNotFoundError)
    async def nf_handler(request: Request, exc: EntityNotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.message})

    return app


@pytest.fixture
def stores():
    return FakeUserRepository(), FakeTokenBlacklist()


@pytest.fixture
async def auth_client(stores) -> AsyncGenerator[tuple[AsyncClient, str], None]:
    user_repo, blacklist = stores
    app = _make_app(user_repo, blacklist)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "pass1234"},
        )
        token = reg.json()["access_token"]
        yield ac, token


async def test_get_my_profile(auth_client):
    client, token = auth_client
    resp = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert data["status"] == "offline"


async def test_update_display_name(auth_client):
    client, token = auth_client
    resp = await client.put(
        "/api/users/me",
        json={"display_name": "Alice Smith"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Alice Smith"


async def test_update_avatar_url(auth_client):
    client, token = auth_client
    resp = await client.put(
        "/api/users/me",
        json={"avatar_url": "https://example.com/avatar.png"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["avatar_url"] == "https://example.com/avatar.png"


async def test_update_status(auth_client):
    client, token = auth_client
    resp = await client.put(
        "/api/users/me",
        json={"status": "online"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"


async def test_update_invalid_status_returns_422(auth_client):
    client, token = auth_client
    resp = await client.put(
        "/api/users/me",
        json={"status": "invisible"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_get_other_user_profile(stores):
    user_repo, blacklist = stores
    app = _make_app(user_repo, blacklist)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/auth/register",
            json={"username": "bob", "email": "bob@example.com", "password": "pass1234"},
        )
        bob_token = r1.json()["access_token"]

        r2 = await ac.post(
            "/api/auth/register",
            json={"username": "carol", "email": "carol@example.com", "password": "pass1234"},
        )
        carol_token = r2.json()["access_token"]

        from src.adapters.api.jwt_utils import decode_token

        carol_id = decode_token(carol_token)["sub"]

        resp = await ac.get(
            f"/api/users/{carol_id}",
            headers={"Authorization": f"Bearer {bob_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "carol"


async def test_get_nonexistent_user_returns_404(auth_client):
    client, token = auth_client
    resp = await client.get(
        f"/api/users/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_profile_requires_auth(stores):
    user_repo, blacklist = stores
    app = _make_app(user_repo, blacklist)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/users/me")
        assert resp.status_code == 422  # missing auth header
