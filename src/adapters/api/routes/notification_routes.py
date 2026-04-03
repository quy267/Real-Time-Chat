"""Notification API routes — list, count unread, mark read."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.notification_schemas import (
    NotificationResponse,
    NotificationsListResponse,
    UnreadCountResponse,
)
from src.domain.exceptions import AuthorizationError, EntityNotFoundError

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _to_response(notification) -> NotificationResponse:
    return NotificationResponse(
        id=str(notification.id),
        type=notification.type,
        title=notification.title,
        content=notification.content,
        reference_id=notification.reference_id,
        read=notification.read,
        created_at=notification.created_at.isoformat(),
    )


@router.get("", response_model=NotificationsListResponse)
async def list_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = False,
    user_id: str = Depends(get_current_user_id),
):
    """List paginated notifications for the authenticated user."""
    from src.adapters.api.dependencies import get_list_notifications_use_case

    uc = get_list_notifications_use_case()
    notifications = await uc.execute(
        user_id=user_id, limit=limit, offset=offset, unread_only=unread_only
    )
    return NotificationsListResponse(
        items=[_to_response(n) for n in notifications],
        limit=limit,
        offset=offset,
    )


@router.get("/count", response_model=UnreadCountResponse)
async def count_unread(user_id: str = Depends(get_current_user_id)):
    """Return the count of unread notifications for the authenticated user."""
    from src.adapters.api.dependencies import get_notification_repo

    repo = get_notification_repo()
    from uuid import UUID

    count = await repo.count_unread(UUID(user_id))
    return UnreadCountResponse(count=count)


@router.put("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(user_id: str = Depends(get_current_user_id)):
    """Mark all notifications as read for the authenticated user."""
    from src.adapters.api.dependencies import get_mark_all_read_use_case

    uc = get_mark_all_read_use_case()
    await uc.execute(user_id=user_id)
    return {"message": "All notifications marked as read"}


@router.put("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Mark a specific notification as read."""
    from src.adapters.api.dependencies import get_mark_notification_read_use_case

    uc = get_mark_notification_read_use_case()
    try:
        await uc.execute(notification_id=notification_id, user_id=user_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except AuthorizationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return {"message": "Notification marked as read"}
