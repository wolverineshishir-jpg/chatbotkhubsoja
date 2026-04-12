from typing import Annotated
from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.membership import Membership
from app.models.user import User
from app.schemas.ai_generation import (
    AIGenerationResponse,
    CommentReplyGenerationRequest,
    InboxReplyGenerationRequest,
    PostGenerationRequest,
)
from app.services.ai.orchestration_service import AIOrchestrationService

router = APIRouter()


@router.post("/generation/inbox-reply", response_model=AIGenerationResponse)
def generate_inbox_reply(
    payload: InboxReplyGenerationRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AIGenerationResponse:
    account, _ = context
    result = AIOrchestrationService(db).generate_inbox_reply(
        account=account,
        conversation_id=payload.conversation_id,
        actor=current_user,
        ai_agent_id=payload.ai_agent_id,
        platform_connection_id=payload.platform_connection_id,
        instructions=payload.instructions,
        send_now=payload.send_now,
        persist_draft=payload.persist_draft,
    )
    return AIGenerationResponse(**asdict(result))


@router.post("/generation/comment-reply", response_model=AIGenerationResponse)
def generate_comment_reply(
    payload: CommentReplyGenerationRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AIGenerationResponse:
    account, _ = context
    result = AIOrchestrationService(db).generate_comment_reply(
        account=account,
        comment_id=payload.comment_id,
        actor=current_user,
        ai_agent_id=payload.ai_agent_id,
        instructions=payload.instructions,
        send_now=payload.send_now,
        persist_draft=payload.persist_draft,
    )
    return AIGenerationResponse(**asdict(result))


@router.post("/generation/post", response_model=AIGenerationResponse)
def generate_post(
    payload: PostGenerationRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AIGenerationResponse:
    account, _ = context
    result = AIOrchestrationService(db).generate_post(
        account=account,
        actor=current_user,
        platform_connection_id=payload.platform_connection_id,
        ai_agent_id=payload.ai_agent_id,
        post_id=payload.post_id,
        title_hint=payload.title_hint,
        instructions=payload.instructions,
        persist_draft=payload.persist_draft,
    )
    return AIGenerationResponse(**asdict(result))
