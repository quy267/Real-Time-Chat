"""Reaction API routes — add, remove, list emoji reactions on messages."""

from fastapi import APIRouter, Depends, status

from src.adapters.api.middleware.jwt_auth_middleware import get_current_user_id
from src.adapters.api.schemas.reaction_schemas import (
    AddReactionRequest,
    ReactionListResponse,
    ReactionResponse,
)
from src.domain.entities.reaction import Reaction
from src.domain.exceptions import DuplicateEntityError, EntityNotFoundError

router = APIRouter(prefix="/api/messages", tags=["reactions"])


def _reaction_response(r: Reaction) -> ReactionResponse:
    return ReactionResponse(
        id=str(r.id),
        message_id=str(r.message_id),
        user_id=str(r.user_id),
        emoji=r.emoji,
        created_at=r.created_at.isoformat(),
    )


@router.post(
    "/{message_id}/reactions",
    response_model=ReactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_reaction(
    message_id: str,
    body: AddReactionRequest,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_add_reaction_use_case

    uc = get_add_reaction_use_case()
    try:
        reaction = await uc.execute(
            message_id=message_id,
            user_id=user_id,
            emoji=body.emoji,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return _reaction_response(reaction)


@router.delete(
    "/{message_id}/reactions/{emoji}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_reaction(
    message_id: str,
    emoji: str,
    user_id: str = Depends(get_current_user_id),
):
    from fastapi import HTTPException

    from src.adapters.api.dependencies import get_remove_reaction_use_case

    uc = get_remove_reaction_use_case()
    try:
        await uc.execute(message_id=message_id, user_id=user_id, emoji=emoji)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.get("/{message_id}/reactions", response_model=ReactionListResponse)
async def list_reactions(
    message_id: str,
    user_id: str = Depends(get_current_user_id),  # noqa: ARG001 — auth required
):
    from src.adapters.api.dependencies import get_list_reactions_use_case

    uc = get_list_reactions_use_case()
    reactions = await uc.execute(message_id=message_id)
    return ReactionListResponse(
        message_id=message_id,
        reactions=[_reaction_response(r) for r in reactions],
        total=len(reactions),
    )
