"""Message API routes — history, edit, delete."""

from fastapi import APIRouter, Depends, Query, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.message_schemas import (
    EditMessageRequest,
    MessageHistoryResponse,
    MessageResponse,
)
from src.domain.entities.message import Message
from src.domain.exceptions import AuthorizationError, EntityNotFoundError

router = APIRouter(prefix="/api", tags=["messages"])


def _msg_response(msg: Message) -> MessageResponse:
    return MessageResponse(
        id=str(msg.id),
        content=msg.content,
        channel_id=str(msg.channel_id),
        user_id=str(msg.user_id),
        thread_id=str(msg.thread_id) if msg.thread_id else None,
        file_url=msg.file_url,
        created_at=msg.created_at.isoformat(),
        updated_at=msg.updated_at.isoformat(),
    )


@router.get("/channels/{channel_id}/messages", response_model=MessageHistoryResponse)
async def get_message_history(
    channel_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: str | None = Query(None, description="Message ID cursor — return messages older than this"),
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_get_message_history_use_case

    uc = get_get_message_history_use_case()
    try:
        messages = await uc.execute(
            channel_id=channel_id,
            user_id=user_id,
            limit=limit,
            before_id=before,
        )
    except AuthorizationError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)

    items = [_msg_response(m) for m in messages]
    next_cursor = items[-1].id if len(items) == limit else None
    return MessageHistoryResponse(items=items, limit=limit, next_cursor=next_cursor)


@router.put("/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: str,
    body: EditMessageRequest,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_edit_message_use_case

    uc = get_edit_message_use_case()
    try:
        message = await uc.execute(
            message_id=message_id,
            user_id=user_id,
            new_content=body.content,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return _msg_response(message)


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_delete_message_use_case

    uc = get_delete_message_use_case()
    try:
        await uc.execute(message_id=message_id, user_id=user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
