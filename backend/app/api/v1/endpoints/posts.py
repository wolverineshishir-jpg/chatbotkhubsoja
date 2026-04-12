from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AuditActionType, AuditResourceType, PostStatus
from app.models.membership import Membership
from app.models.user import User
from app.schemas.posts import (
    PostApprovalRequest,
    PostRejectRequest,
    PostScheduleRequest,
    SocialPostCreateRequest,
    SocialPostListResponse,
    SocialPostResponse,
    SocialPostUpdateRequest,
)
from app.services.post_service import PostService
from app.services.audit_log_service import AuditContext, AuditLogService

router = APIRouter()


@router.get("", response_model=SocialPostListResponse)
def list_posts(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:read"))],
    db: Session = Depends(get_db),
    status_filter: Annotated[PostStatus | None, Query(alias="status")] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SocialPostListResponse:
    account, _ = context
    return PostService(db).list_posts(account=account, status_filter=status_filter, page=page, page_size=page_size)


@router.post("", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    request: Request,
    payload: SocialPostCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SocialPostResponse:
    account, _ = context
    response = PostService(db).create_post(account=account, actor=current_user, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.POST_CREATED,
        resource_type=AuditResourceType.SOCIAL_POST,
        resource_id=str(response.id),
        description=f'Created post "{response.title or "Untitled post"}".',
        metadata_json={"status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.get("/{post_id}", response_model=SocialPostResponse)
def get_post(
    post_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:read"))],
    db: Session = Depends(get_db),
) -> SocialPostResponse:
    account, _ = context
    return PostService(db).get_post(account=account, post_id=post_id)


@router.put("/{post_id}", response_model=SocialPostResponse)
def update_post(
    request: Request,
    post_id: int,
    payload: SocialPostUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SocialPostResponse:
    account, _ = context
    response = PostService(db).update_post(account=account, post_id=post_id, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.POST_UPDATED,
        resource_type=AuditResourceType.SOCIAL_POST,
        resource_id=str(response.id),
        description=f'Updated post "{response.title or "Untitled post"}".',
        metadata_json={"status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_post(
    post_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:manage"))],
    db: Session = Depends(get_db),
) -> Response:
    account, _ = context
    PostService(db).delete_post(account=account, post_id=post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{post_id}/approve", response_model=SocialPostResponse)
def approve_post(
    request: Request,
    post_id: int,
    payload: PostApprovalRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SocialPostResponse:
    account, _ = context
    response = PostService(db).approve_post(account=account, actor=current_user, post_id=post_id, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.POST_APPROVED,
        resource_type=AuditResourceType.SOCIAL_POST,
        resource_id=str(response.id),
        description="Approved post.",
        metadata_json={"note": payload.note},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/{post_id}/reject", response_model=SocialPostResponse)
def reject_post(
    request: Request,
    post_id: int,
    payload: PostRejectRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SocialPostResponse:
    account, _ = context
    response = PostService(db).reject_post(account=account, actor=current_user, post_id=post_id, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.POST_REJECTED,
        resource_type=AuditResourceType.SOCIAL_POST,
        resource_id=str(response.id),
        description="Rejected post.",
        metadata_json={"reason": payload.reason},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/{post_id}/schedule", response_model=SocialPostResponse)
def schedule_post(
    request: Request,
    post_id: int,
    payload: PostScheduleRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SocialPostResponse:
    account, _ = context
    response = PostService(db).schedule_post(account=account, post_id=post_id, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.POST_SCHEDULED,
        resource_type=AuditResourceType.SOCIAL_POST,
        resource_id=str(response.id),
        description="Scheduled post for publishing.",
        metadata_json={"scheduled_for": payload.scheduled_for.isoformat()},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/{post_id}/publish-now", response_model=SocialPostResponse)
def publish_post_now(
    request: Request,
    post_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("posts:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SocialPostResponse:
    account, _ = context
    response = PostService(db).publish_now(account=account, post_id=post_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.POST_PUBLISH_NOW,
        resource_type=AuditResourceType.SOCIAL_POST,
        resource_id=str(response.id),
        description="Queued post for immediate publishing.",
        metadata_json={"status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response
