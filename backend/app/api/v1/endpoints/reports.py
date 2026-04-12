from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AuditActionType, AuditResourceType
from app.models.membership import Membership
from app.models.user import User
from app.schemas.reports import (
    BillingSummaryResponse,
    CommentStatsResponse,
    ConversationStatsResponse,
    DashboardSummaryResponse,
    PostStatsResponse,
    TokenUsageSummaryResponse,
)
from app.services.audit_log_service import AuditContext, AuditLogService
from app.services.reporting_service import ReportingService

router = APIRouter()


@router.get("/dashboard-summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    request: Request,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    account, _ = context
    result = ReportingService(db).dashboard_summary(account=account)
    _record_report_view(db, account, current_user, request, "dashboard_summary")
    return result


@router.get("/token-usage-summary", response_model=TokenUsageSummaryResponse)
def get_token_usage_summary(
    request: Request,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TokenUsageSummaryResponse:
    account, _ = context
    result = ReportingService(db).token_usage_summary(account=account)
    _record_report_view(db, account, current_user, request, "token_usage_summary")
    return result


@router.get("/billing-summary", response_model=BillingSummaryResponse)
def get_billing_summary(
    request: Request,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> BillingSummaryResponse:
    account, _ = context
    result = ReportingService(db).billing_summary(account=account)
    _record_report_view(db, account, current_user, request, "billing_summary")
    return result


@router.get("/conversation-stats", response_model=ConversationStatsResponse)
def get_conversation_stats(
    request: Request,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> ConversationStatsResponse:
    account, _ = context
    result = ReportingService(db).conversation_stats(account=account)
    _record_report_view(db, account, current_user, request, "conversation_stats")
    return result


@router.get("/comment-stats", response_model=CommentStatsResponse)
def get_comment_stats(
    request: Request,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> CommentStatsResponse:
    account, _ = context
    result = ReportingService(db).comment_stats(account=account)
    _record_report_view(db, account, current_user, request, "comment_stats")
    return result


@router.get("/post-stats", response_model=PostStatsResponse)
def get_post_stats(
    request: Request,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> PostStatsResponse:
    account, _ = context
    result = ReportingService(db).post_stats(account=account)
    _record_report_view(db, account, current_user, request, "post_stats")
    return result


def _record_report_view(db: Session, account: Account, actor: User, request: Request, report_name: str) -> None:
    AuditLogService(db).record(
        account=account,
        actor=actor,
        action_type=AuditActionType.REPORT_VIEWED,
        resource_type=AuditResourceType.REPORT,
        resource_id=report_name,
        description=f"Viewed {report_name.replace('_', ' ')} report.",
        metadata_json={"report_name": report_name},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
