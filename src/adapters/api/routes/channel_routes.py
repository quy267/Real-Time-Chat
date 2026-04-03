"""Channel API routes — CRUD and membership management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.channel_schemas import (
    ChannelResponse,
    CreateChannelRequest,
    MemberResponse,
    PaginatedResponse,
    UpdateChannelRequest,
)
from src.domain.exceptions import (
    AuthorizationError,
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)

router = APIRouter(prefix="/api/channels", tags=["channels"])


def _channel_response(channel) -> ChannelResponse:
    return ChannelResponse(
        id=str(channel.id),
        name=channel.name,
        description=channel.description,
        channel_type=channel.channel_type.value,
        creator_id=str(channel.creator_id),
        created_at=channel.created_at.isoformat(),
        updated_at=channel.updated_at.isoformat(),
    )


def _member_response(membership) -> MemberResponse:
    return MemberResponse(
        user_id=str(membership.user_id),
        channel_id=str(membership.channel_id),
        role=membership.role.value,
        joined_at=membership.joined_at.isoformat(),
    )


@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    body: CreateChannelRequest,
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_create_channel_use_case

    uc = get_create_channel_use_case()
    try:
        channel = await uc.execute(
            name=body.name,
            description=body.description,
            channel_type=body.channel_type,
            creator_id=user_id,
        )
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    return _channel_response(channel)


@router.get("", response_model=PaginatedResponse)
async def list_channels(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_list_channels_use_case

    uc = get_list_channels_use_case()
    channels = await uc.execute(user_id=user_id, limit=limit, offset=offset)
    items = [_channel_response(c) for c in channels]
    return PaginatedResponse(items=items, total=len(items), limit=limit, offset=offset)


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: str,
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_get_channel_use_case

    uc = get_get_channel_use_case()
    try:
        channel = await uc.execute(channel_id=channel_id, user_id=user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return _channel_response(channel)


@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: str,
    body: UpdateChannelRequest,
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_update_channel_use_case

    uc = get_update_channel_use_case()
    try:
        channel = await uc.execute(
            channel_id=channel_id,
            user_id=user_id,
            name=body.name,
            description=body.description,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return _channel_response(channel)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: str,
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_delete_channel_use_case

    uc = get_delete_channel_use_case()
    try:
        await uc.execute(channel_id=channel_id, user_id=user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.post("/{channel_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def join_channel(
    channel_id: str,
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_join_channel_use_case

    uc = get_join_channel_use_case()
    try:
        membership = await uc.execute(channel_id=channel_id, user_id=user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return _member_response(membership)


@router.delete("/{channel_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_channel(
    channel_id: str,
    target_user_id: str,
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_leave_channel_use_case

    if user_id != target_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only remove yourself from a channel")

    uc = get_leave_channel_use_case()
    try:
        await uc.execute(channel_id=channel_id, user_id=target_user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


@router.get("/{channel_id}/members", response_model=PaginatedResponse)
async def list_members(
    channel_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_list_members_use_case

    uc = get_list_members_use_case()
    try:
        members = await uc.execute(
            channel_id=channel_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    items = [_member_response(m) for m in members]
    return PaginatedResponse(items=items, total=len(items), limit=limit, offset=offset)
