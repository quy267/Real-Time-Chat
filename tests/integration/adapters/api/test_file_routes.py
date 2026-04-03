"""Integration tests for file upload API routes using fake storage."""

import io
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes.fake_token_blacklist import FakeTokenBlacklist
from tests.fakes.fake_user_repository import FakeUserRepository


def _make_app(user_repo, blacklist, upload_dir: str):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    import src.adapters.api.dependencies as deps
    from src.adapters.api.bcrypt_password_service import BcryptPasswordService
    from src.adapters.api.jwt_token_service import JwtTokenService
    from src.adapters.api.routes.auth_routes import router as auth_router
    from src.adapters.api.routes.file_routes import router as file_router
    from src.adapters.storage.local_file_storage import LocalFileStorage
    from src.domain.exceptions import AuthenticationError, ValidationError
    from src.use_cases.auth.login_user import LoginUserUseCase
    from src.use_cases.auth.logout_user import LogoutUserUseCase
    from src.use_cases.auth.refresh_token import RefreshTokenUseCase
    from src.use_cases.auth.register_user import RegisterUserUseCase
    from src.use_cases.files.upload_file import UploadFileUseCase

    storage = LocalFileStorage(upload_dir=upload_dir, max_size_bytes=10 * 1024 * 1024)

    deps.get_register_use_case = lambda: RegisterUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_login_use_case = lambda: LoginUserUseCase(user_repo, BcryptPasswordService(), JwtTokenService())
    deps.get_refresh_use_case = lambda: RefreshTokenUseCase(blacklist, JwtTokenService())
    deps.get_logout_use_case = lambda: LogoutUserUseCase(blacklist)
    deps.get_upload_file_use_case = lambda: UploadFileUseCase(storage)

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(file_router)

    @app.exception_handler(ValidationError)
    async def val_handler(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.message})

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    return app


@pytest.fixture
def stores():
    return FakeUserRepository(), FakeTokenBlacklist()


@pytest.fixture
async def auth_client(stores, tmp_path) -> AsyncGenerator[tuple[AsyncClient, str], None]:
    user_repo, blacklist = stores
    app = _make_app(user_repo, blacklist, str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post(
            "/api/auth/register",
            json={"username": "alice", "email": "alice@example.com", "password": "pass1234"},
        )
        token = reg.json()["access_token"]
        yield ac, token


async def test_upload_image_success(auth_client):
    client, token = auth_client
    resp = await client.post(
        "/api/files/upload",
        files={"file": ("photo.png", io.BytesIO(b"fake-png"), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["url"].startswith("/uploads/")
    assert data["filename"] == "photo.png"
    assert data["content_type"] == "image/png"
    assert data["size_bytes"] == len(b"fake-png")


async def test_upload_text_file_success(auth_client):
    client, token = auth_client
    content = b"hello world"
    resp = await client.post(
        "/api/files/upload",
        files={"file": ("readme.txt", io.BytesIO(content), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["url"].startswith("/uploads/")


async def test_upload_disallowed_type_returns_422(auth_client):
    client, token = auth_client
    resp = await client.post(
        "/api/files/upload",
        files={"file": ("virus.exe", io.BytesIO(b"MZ\x90"), "application/x-msdownload")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_upload_oversized_file_returns_422(auth_client):
    client, token = auth_client
    big = b"x" * (10 * 1024 * 1024 + 1)
    resp = await client.post(
        "/api/files/upload",
        files={"file": ("big.png", io.BytesIO(big), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_upload_requires_auth(stores, tmp_path):
    user_repo, blacklist = stores
    app = _make_app(user_repo, blacklist, str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/files/upload",
            files={"file": ("photo.png", io.BytesIO(b"data"), "image/png")},
        )
        assert resp.status_code == 422  # missing auth header
