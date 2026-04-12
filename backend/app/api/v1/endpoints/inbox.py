from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AuditActionType, AuditResourceType, ConversationStatus, PlatformType
from app.models.membership import Membership
from app.models.user import User
from app.schemas.inbox import (
    ConversationAssignRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationStatusUpdateRequest,
    ConversationSummaryResponse,
    MessageListResponse,
    MessageResponse,
    SendReplyRequest,
)
from app.services.inbox_service import InboxService
from app.services.audit_log_service import AuditContext, AuditLogService

router = APIRouter()


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("inbox:read"))],
    db: Session = Depends(get_db),
    status_filter: Annotated[ConversationStatus | None, Query(alias="status")] = None,
    platform: PlatformType | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=255),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ConversationListResponse:
    account, _ = context
    return InboxService(db).list_conversations(
        account=account,
        status_filter=status_filter,
        platform_filter=platform,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_detail(
    conversation_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("inbox:read"))],
    db: Session = Depends(get_db),
) -> ConversationDetailResponse:
    account, _ = context
    return InboxService(db).get_conversation_detail(account=account, conversation_id=conversation_id)


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
def list_conversation_messages(
    conversation_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("inbox:read"))],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
) -> MessageListResponse:
    account, _ = context
    return InboxService(db).list_messages(account=account, conversation_id=conversation_id, page=page, page_size=page_size)


@router.post("/conversations/{conversation_id}/assign", response_model=ConversationSummaryResponse)
def assign_conversation(
    request: Request,
    conversation_id: int,
    payload: ConversationAssignRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("inbox:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ConversationSummaryResponse:
    account, _ = context
    response = InboxService(db).assign_conversation(account=account, payload=payload, conversation_id=conversation_id)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONVERSATION_ASSIGNED,
        resource_type=AuditResourceType.CONVERSATION,
        resource_id=str(conversation_id),
        description="Updated conversation assignee.",
        metadata_json={"assignee_user_id": payload.assignee_user_id},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.patch("/conversations/{conversation_id}/status", response_model=ConversationSummaryResponse)
def update_conversation_status(
    request: Request,
    conversation_id: int,
    payload: ConversationStatusUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("inbox:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ConversationSummaryResponse:
    account, _ = context
    response = InboxService(db).update_conversation_status(account=account, conversation_id=conversation_id, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.CONVERSATION_STATUS_UPDATED,
        resource_type=AuditResourceType.CONVERSATION,
        resource_id=str(conversation_id),
        description=f"Updated conversation status to {payload.status.value}.",
        metadata_json={"paused_until": payload.paused_until.isoformat() if payload.paused_until else None},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post(
    "/conversations/{conversation_id}/reply",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_reply(
    request: Request,
    conversation_id: int,
    payload: SendReplyRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("inbox:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> MessageResponse:
    account, _ = context
    response = InboxService(db).send_reply(account=account, actor=current_user, conversation_id=conversation_id, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.MESSAGE_REPLY_SENT,
        resource_type=AuditResourceType.MESSAGE,
        resource_id=str(response.id),
        description="Sent conversation reply.",
        metadata_json={"conversation_id": conversation_id, "sender_type": payload.sender_type.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response
