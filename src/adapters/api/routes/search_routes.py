"""Search API routes — full-text search for messages and channels."""

from fastapi import APIRouter, Depends, Query

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.search_schemas import SearchChannelsResult, SearchMessagesResult
from src.domain.entities.channel import Channel
from src.domain.entities.message import Message

router = APIRouter(prefix="/api/search", tags=["search"])


def _msg_item(msg: Message) -> dict:
    return {
        "id": str(msg.id),
        "content": msg.content,
        "channel_id": str(msg.channel_id),
        "user_id": str(msg.user_id),
        "created_at": msg.created_at.isoformat(),
    }


def _channel_item(ch: Channel) -> dict:
    return {
        "id": str(ch.id),
        "name": ch.name,
        "description": ch.description,
        "channel_type": ch.channel_type.value,
    }


@router.get("/messages", response_model=SearchMessagesResult)
async def search_messages(
    q: str = Query(..., min_length=1, description="Search query"),
    channel_id: str | None = Query(None, description="Restrict search to a specific channel"),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_search_messages_use_case

    uc = get_search_messages_use_case()
    results = await uc.execute(query=q, user_id=user_id, channel_id=channel_id, limit=limit)
    items = [_msg_item(m) for m in results]
    return SearchMessagesResult(query=q, items=items, total=len(items))


@router.get("/channels", response_model=SearchChannelsResult)
async def search_channels(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_search_channels_use_case

    uc = get_search_channels_use_case()
    results = await uc.execute(query=q, user_id=user_id, limit=limit)
    items = [_channel_item(c) for c in results]
    return SearchChannelsResult(query=q, items=items, total=len(items))
