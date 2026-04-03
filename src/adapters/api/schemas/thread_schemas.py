"""Pydantic schemas for thread API requests and responses."""

from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    pass  # thread is created from message_id path param only


class ThreadResponse(BaseModel):
    id: str
    channel_id: str
    parent_message_id: str
    created_at: str


class ThreadReplyRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class ThreadReplyResponse(BaseModel):
    id: str
    content: str
    channel_id: str
    user_id: str
    thread_id: str
    created_at: str
    updated_at: str


class ThreadRepliesResponse(BaseModel):
    items: list[ThreadReplyResponse]
    limit: int
    next_cursor: str | None
