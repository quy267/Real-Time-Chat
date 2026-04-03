"""FastAPI dependency for JWT Bearer token authentication."""

import jwt
from fastapi import Header, HTTPException, status

from src.adapters.api.jwt_utils import decode_token


async def get_current_user_id(authorization: str = Header(...)) -> str:
    """Extract and validate Bearer JWT from Authorization header.

    Returns the user_id (sub claim) on success.
    Raises HTTP 401 on missing, malformed, expired, or wrong-type token.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization.startswith("Bearer "):
        raise credentials_error

    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_error

    if payload.get("type") != "access":
        raise credentials_error

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_error

    return user_id
