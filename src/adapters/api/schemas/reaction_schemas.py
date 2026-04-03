"""Pydantic schemas for reaction API requests and responses."""

from pydantic import BaseModel, Field


class AddReactionRequest(BaseModel):
    emoji: str = Field(..., min_length=1, max_length=32)


class ReactionResponse(BaseModel):
    id: str
    message_id: str
    user_id: str
    emoji: str
    created_at: str


class ReactionListResponse(BaseModel):
    message_id: str
    reactions: list[ReactionResponse]
    total: int
