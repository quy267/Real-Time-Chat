"""Thread API routes — create thread, reply, and fetch replies."""

from fastapi import APIRouter, Depends, Query, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.thread_schemas import (
    ThreadRepliesResponse,
    ThreadReplyRequest,
    ThreadReplyResponse,
    ThreadResponse,
)
from src.domain.exceptions import AuthorizationError, DuplicateEntityError, EntityNotFoundError

router = APIRouter(prefix="/api", tags=["threads"])


def _thread_response(thread) -> ThreadResponse:
    return ThreadResponse(
        id=str(thread.id),
        channel_id=str(thread.channel_id),
        parent_message_id=str(thread.parent_message_id),
        created_at=thread.created_at.isoformat(),
    )


def _reply_response(msg) -> ThreadReplyResponse:
    return ThreadReplyResponse(
        id=str(msg.id),
        content=msg.content,
        channel_id=str(msg.channel_id),
        user_id=str(msg.user_id),
        thread_id=str(msg.thread_id),
        created_at=msg.created_at.isoformat(),
        updated_at=msg.updated_at.isoformat(),
    )


@router.post(
    "/messages/{message_id}/thread",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_create_thread_use_case

    uc = get_create_thread_use_case()
    try:
        thread = await uc.execute(parent_message_id=message_id, user_id=user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return _thread_response(thread)


@router.post(
    "/threads/{thread_id}/replies",
    response_model=ThreadReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reply_to_thread(
    thread_id: str,
    body: ThreadReplyRequest,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_reply_to_thread_use_case

    uc = get_reply_to_thread_use_case()
    try:
        message = await uc.execute(thread_id=thread_id, user_id=user_id, content=body.content)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return _reply_response(message)


@router.get("/threads/{thread_id}/replies", response_model=ThreadRepliesResponse)
async def get_thread_replies(
    thread_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: str | None = Query(None, description="Message ID cursor"),
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_thread_replies_use_case

    uc = get_thread_replies_use_case()
    try:
        messages = await uc.execute(
            thread_id=thread_id,
            user_id=user_id,
            limit=limit,
            before_id=before,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)

    items = [_reply_response(m) for m in messages]
    next_cursor = items[-1].id if len(items) == limit else None
    return ThreadRepliesResponse(items=items, limit=limit, next_cursor=next_cursor)
