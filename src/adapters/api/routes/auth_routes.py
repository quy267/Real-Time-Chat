"""Auth API routes — register, login, refresh, logout."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.auth_schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from src.domain.exceptions import AuthenticationError, DuplicateEntityError, ValidationError

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_response(token_pair) -> TokenResponse:
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """Register a new user and return a token pair."""
    from src.adapters.api.dependencies import get_register_use_case

    uc = get_register_use_case()
    try:
        token_pair = await uc.execute(body.username, body.email, body.password)
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    return _token_response(token_pair)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Authenticate user and return a token pair."""
    from src.adapters.api.dependencies import get_login_use_case

    uc = get_login_use_case()
    try:
        token_pair = await uc.execute(body.email, body.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    return _token_response(token_pair)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    """Exchange a valid refresh token for a new token pair."""
    from src.adapters.api.dependencies import get_refresh_use_case

    uc = get_refresh_use_case()
    try:
        token_pair = await uc.execute(body.refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    return _token_response(token_pair)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(body: RefreshRequest):
    """Blacklist a refresh token (logout)."""
    from src.adapters.api.dependencies import get_logout_use_case

    uc = get_logout_use_case()
    await uc.execute(body.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def me(user_id: str = Depends(get_current_user_id)):
    """Protected endpoint — returns the authenticated user's id."""
    return {"user_id": user_id}
