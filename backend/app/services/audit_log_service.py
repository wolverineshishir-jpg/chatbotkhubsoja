from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.audit_log import AuditLog
from app.models.enums import AuditActionType, AuditResourceType
from app.models.user import User
from app.schemas.observability import AuditLogListResponse, AuditLogResponse


@dataclass(slots=True)
class AuditContext:
    ip_address: str | None = None
    user_agent: str | None = None


class AuditLogService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        account: Account,
        action_type: AuditActionType,
        resource_type: AuditResourceType,
        description: str,
        actor: User | None = None,
        resource_id: str | None = None,
        metadata_json: dict[str, Any] | None = None,
        context: AuditContext | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            account_id=account.id,
            actor_user_id=actor.id if actor else None,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=context.ip_address if context else None,
            user_agent=context.user_agent if context else None,
            occurred_at=self._utcnow(),
            metadata_json=metadata_json or {},
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_logs(
        self,
        *,
        account: Account,
        page: int,
        page_size: int,
        action_type: AuditActionType | None = None,
    ) -> AuditLogListResponse:
        statement = select(AuditLog).where(AuditLog.account_id == account.id)
        count_statement = select(func.count(AuditLog.id)).where(AuditLog.account_id == account.id)
        if action_type:
            statement = statement.where(AuditLog.action_type == action_type)
            count_statement = count_statement.where(AuditLog.action_type == action_type)

        statement = statement.order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())
        total = self.db.scalar(count_statement) or 0
        items = self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        return AuditLogListResponse(
            items=[AuditLogResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
