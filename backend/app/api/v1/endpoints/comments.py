from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AuditActionType, AuditResourceType, CommentStatus
from app.models.membership import Membership
from app.models.user import User
from app.schemas.comments import (
    FacebookCommentDetailResponse,
    FacebookCommentListResponse,
    FacebookCommentReplyCreateRequest,
    FacebookCommentReplyResponse,
    FacebookCommentStatusUpdateRequest,
    FacebookCommentSummaryResponse,
)
from app.services.comment_moderation_service import CommentModerationService
from app.services.audit_log_service import AuditContext, AuditLogService

router = APIRouter()


@router.get("", response_model=FacebookCommentListResponse)
def list_comments(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("comments:read"))],
    db: Session = Depends(get_db),
    status_filter: Annotated[CommentStatus | None, Query(alias="status")] = None,
    search: str | None = Query(default=None, min_length=1, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> FacebookCommentListResponse:
    account, _ = context
    return CommentModerationService(db).list_comments(
        account=account,
        status_filter=status_filter,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/{comment_id}", response_model=FacebookCommentDetailResponse)
def get_comment_detail(
    comment_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("comments:read"))],
    db: Session = Depends(get_db),
) -> FacebookCommentDetailResponse:
    account, _ = context
    return CommentModerationService(db).get_comment_detail(account=account, comment_id=comment_id)


@router.patch("/{comment_id}/status", response_model=FacebookCommentSummaryResponse)
def update_comment_status(
    request: Request,
    comment_id: int,
    payload: FacebookCommentStatusUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("comments:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FacebookCommentSummaryResponse:
    account, _ = context
    response = CommentModerationService(db).update_comment_status(account=account, comment_id=comment_id, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.COMMENT_STATUS_UPDATED,
        resource_type=AuditResourceType.FACEBOOK_COMMENT,
        resource_id=str(comment_id),
        description=f"Updated comment status to {response.status.value}.",
        metadata_json={"assignee_user_id": payload.assignee_user_id},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get('user-agent')),
    )
    return response


@router.post("/{comment_id}/replies", response_model=FacebookCommentReplyResponse, status_code=status.HTTP_201_CREATED)
def create_comment_reply(
    request: Request,
    comment_id: int,
    payload: FacebookCommentReplyCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("comments:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> FacebookCommentReplyResponse:
    account, _ = context
    response = CommentModerationService(db).create_reply(
        account=account,
        actor=current_user,
        comment_id=comment_id,
        payload=payload,
    )
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.COMMENT_REPLY_CREATED,
        resource_type=AuditResourceType.FACEBOOK_COMMENT_REPLY,
        resource_id=str(response.id),
        description="Created comment reply.",
        metadata_json={"comment_id": comment_id, "send_now": payload.send_now},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get('user-agent')),
    )
    return response
