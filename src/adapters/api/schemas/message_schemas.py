"""Pydantic schemas for message API requests and responses."""

from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    thread_id: str | None = None
    file_url: str | None = None


class EditMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    id: str
    content: str
    channel_id: str
    user_id: str
    thread_id: str | None
    file_url: str | None
    created_at: str
    updated_at: str


class MessageHistoryResponse(BaseModel):
    items: list[MessageResponse]
    limit: int
    next_cursor: str | None  # message_id to pass as before_id for next page
