"""User profile API routes — get and update user profiles."""

from fastapi import APIRouter, Depends, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.user_schemas import UpdateProfileRequest, UserProfileResponse
from src.domain.entities.user import User
from src.domain.exceptions import EntityNotFoundError, ValidationError

router = APIRouter(prefix="/api/users", tags=["users"])


def _profile_response(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        id=str(user.id),
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        status=user.status.value,
        created_at=user.created_at.isoformat(),
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_user_profile_use_case

    uc = get_user_profile_use_case()
    try:
        user = await uc.execute(user_id=user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return _profile_response(user)


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    body: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_update_user_profile_use_case

    uc = get_update_user_profile_use_case()
    try:
        user = await uc.execute(
            user_id=user_id,
            display_name=body.display_name,
            avatar_url=body.avatar_url,
            status=body.status,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    return _profile_response(user)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    _current_user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_user_profile_use_case

    uc = get_user_profile_use_case()
    try:
        user = await uc.execute(user_id=user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return _profile_response(user)
