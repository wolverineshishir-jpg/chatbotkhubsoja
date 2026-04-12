from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.membership import Membership
from app.models.user import User
from app.schemas.observability import (
    ActionUsageLogCreateRequest,
    ActionUsageLogListResponse,
    ActionUsageLogResponse,
    AuditLogListResponse,
    LLMTokenUsageCreateRequest,
    LLMTokenUsageListResponse,
    LLMTokenUsageResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.observability_service import ObservabilityService

router = APIRouter()


@router.get("/action-usage-logs", response_model=ActionUsageLogListResponse)
def list_action_usage_logs(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ActionUsageLogListResponse:
    account, _ = context
    return ObservabilityService(db).list_action_usage_logs(account=account, page=page, page_size=page_size)


@router.post("/action-usage-logs", response_model=ActionUsageLogResponse, status_code=status.HTTP_201_CREATED)
def create_action_usage_log(
    payload: ActionUsageLogCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ActionUsageLogResponse:
    account, _ = context
    return ObservabilityService(db).create_action_usage_log(account=account, actor=current_user, payload=payload)


@router.get("/llm-token-usage", response_model=LLMTokenUsageListResponse)
def list_llm_token_usage(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> LLMTokenUsageListResponse:
    account, _ = context
    return ObservabilityService(db).list_llm_token_usage(account=account, page=page, page_size=page_size)


@router.post("/llm-token-usage", response_model=LLMTokenUsageResponse, status_code=status.HTTP_201_CREATED)
def create_llm_token_usage(
    payload: LLMTokenUsageCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> LLMTokenUsageResponse:
    account, _ = context
    return ObservabilityService(db).create_llm_token_usage(account=account, actor=current_user, payload=payload)


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AuditLogListResponse:
    account, _ = context
    return AuditLogService(db).list_logs(account=account, page=page, page_size=page_size)
