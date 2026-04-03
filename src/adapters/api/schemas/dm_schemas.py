"""Pydantic schemas for direct message API requests and responses."""

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    other_user_id: str


class ConversationResponse(BaseModel):
    id: str
    created_at: str


class ConversationsListResponse(BaseModel):
    items: list[ConversationResponse]
    limit: int
    offset: int


class SendDmRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class DmMessageResponse(BaseModel):
    id: str
    content: str
    conversation_id: str
    user_id: str
    created_at: str
    updated_at: str


class DmHistoryResponse(BaseModel):
    items: list[DmMessageResponse]
    limit: int
    next_cursor: str | None
