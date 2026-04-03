"""Pydantic schemas for notification API requests and responses."""


from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    content: str
    reference_id: str | None
    read: bool
    created_at: str


class NotificationsListResponse(BaseModel):
    items: list[NotificationResponse]
    limit: int
    offset: int


class UnreadCountResponse(BaseModel):
    count: int
