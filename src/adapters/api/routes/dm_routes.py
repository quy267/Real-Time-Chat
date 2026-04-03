"""Direct Message API routes — conversations and DM messages."""

from fastapi import APIRouter, Depends, Query, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.dm_schemas import (
    ConversationResponse,
    ConversationsListResponse,
    CreateConversationRequest,
    DmHistoryResponse,
    DmMessageResponse,
    SendDmRequest,
)
from src.domain.exceptions import AuthorizationError, EntityNotFoundError, ValidationError

router = APIRouter(prefix="/api/dm", tags=["direct-messages"])


def _conv_response(conv) -> ConversationResponse:
    return ConversationResponse(
        id=str(conv.id),
        created_at=conv.created_at.isoformat(),
    )


def _dm_msg_response(msg, conversation_id: str) -> DmMessageResponse:
    return DmMessageResponse(
        id=str(msg.id),
        content=msg.content,
        conversation_id=conversation_id,
        user_id=str(msg.user_id),
        created_at=msg.created_at.isoformat(),
        updated_at=msg.updated_at.isoformat(),
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    body: CreateConversationRequest,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_create_conversation_use_case

    uc = get_create_conversation_use_case()
    try:
        conv = await uc.execute(creator_id=user_id, other_user_id=body.other_user_id)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    return _conv_response(conv)


@router.get("/conversations", response_model=ConversationsListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_list_conversations_use_case

    uc = get_list_conversations_use_case()
    convs = await uc.execute(user_id=user_id, limit=limit, offset=offset)
    items = [_conv_response(c) for c in convs]
    return ConversationsListResponse(items=items, limit=limit, offset=offset)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=DmMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_direct_message(
    conversation_id: str,
    body: SendDmRequest,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_send_dm_use_case

    uc = get_send_dm_use_case()
    try:
        msg = await uc.execute(
            conversation_id=conversation_id,
            user_id=user_id,
            content=body.content,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
    return _dm_msg_response(msg, conversation_id)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=DmHistoryResponse,
)
async def get_dm_history(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: str | None = Query(None, description="Message ID cursor"),
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_dm_history_use_case

    uc = get_dm_history_use_case()
    try:
        messages = await uc.execute(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            before_id=before,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)

    items = [_dm_msg_response(m, conversation_id) for m in messages]
    next_cursor = items[-1].id if len(items) == limit else None
    return DmHistoryResponse(items=items, limit=limit, next_cursor=next_cursor)
