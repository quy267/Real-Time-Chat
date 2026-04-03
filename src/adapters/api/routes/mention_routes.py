"""Mention API routes — list @mentions for the current user."""

from fastapi import APIRouter, Depends, Query

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id

router = APIRouter(prefix="/api", tags=["mentions"])


class MentionResponse:
    pass


@router.get("/mentions")
async def list_mentions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    from src.adapters.api.dependencies import get_list_mentions_use_case

    uc = get_list_mentions_use_case()
    mentions = await uc.execute(user_id=user_id, limit=limit, offset=offset)
    return {
        "items": [
            {
                "id": str(m.id),
                "message_id": str(m.message_id),
                "mentioned_user_id": str(m.mentioned_user_id),
                "created_at": m.created_at.isoformat(),
            }
            for m in mentions
        ],
        "limit": limit,
        "offset": offset,
    }
