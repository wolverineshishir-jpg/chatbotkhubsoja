from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.action_usage_log import ActionUsageLog
from app.models.enums import ActionUsageType, PlatformType
from app.models.llm_token_usage import LLMTokenUsage
from app.models.user import User
from app.schemas.observability import (
    ActionUsageLogCreateRequest,
    ActionUsageLogListResponse,
    ActionUsageLogResponse,
    LLMTokenUsageCreateRequest,
    LLMTokenUsageListResponse,
    LLMTokenUsageResponse,
)


class ObservabilityService:
    def __init__(self, db: Session):
        self.db = db

    def create_action_usage_log(
        self,
        *,
        account: Account,
        actor: User | None,
        payload: ActionUsageLogCreateRequest,
    ) -> ActionUsageLogResponse:
        entry = ActionUsageLog(
            account_id=account.id,
            platform_connection_id=payload.platform_connection_id,
            actor_user_id=actor.id if actor else None,
            action_type=payload.action_type,
            platform_type=payload.platform_type,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            quantity=payload.quantity,
            tokens_consumed=payload.tokens_consumed,
            estimated_cost=float(payload.estimated_cost),
            occurred_at=payload.occurred_at or self._utcnow(),
            metadata_json=payload.metadata_json,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return ActionUsageLogResponse.model_validate(entry)

    def record_action_usage(
        self,
        *,
        account_id: int,
        action_type: ActionUsageType,
        actor_user_id: int | None = None,
        platform_connection_id: int | None = None,
        platform_type: PlatformType | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
        quantity: int = 1,
        tokens_consumed: int = 0,
        estimated_cost: Decimal = Decimal("0"),
        occurred_at: datetime | None = None,
        metadata_json: dict | None = None,
    ) -> ActionUsageLog:
        entry = ActionUsageLog(
            account_id=account_id,
            platform_connection_id=platform_connection_id,
            actor_user_id=actor_user_id,
            action_type=action_type,
            platform_type=platform_type,
            reference_type=reference_type,
            reference_id=reference_id,
            quantity=quantity,
            tokens_consumed=tokens_consumed,
            estimated_cost=float(estimated_cost),
            occurred_at=occurred_at or self._utcnow(),
            metadata_json=metadata_json or {},
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_action_usage_logs(
        self,
        *,
        account: Account,
        page: int,
        page_size: int,
    ) -> ActionUsageLogListResponse:
        statement = (
            select(ActionUsageLog)
            .where(ActionUsageLog.account_id == account.id)
            .order_by(ActionUsageLog.occurred_at.desc(), ActionUsageLog.id.desc())
        )
        total = self.db.scalar(
            select(func.count(ActionUsageLog.id)).where(ActionUsageLog.account_id == account.id)
        ) or 0
        items = self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        return ActionUsageLogListResponse(
            items=[ActionUsageLogResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def create_llm_token_usage(
        self,
        *,
        account: Account,
        actor: User | None,
        payload: LLMTokenUsageCreateRequest,
    ) -> LLMTokenUsageResponse:
        entry = LLMTokenUsage(
            account_id=account.id,
            platform_connection_id=payload.platform_connection_id,
            actor_user_id=actor.id if actor else None,
            provider=payload.provider.strip(),
            model_name=payload.model_name.strip(),
            feature_name=payload.feature_name.strip(),
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            prompt_tokens=payload.prompt_tokens,
            completion_tokens=payload.completion_tokens,
            total_tokens=payload.total_tokens or (payload.prompt_tokens + payload.completion_tokens),
            estimated_cost=float(payload.estimated_cost),
            request_count=payload.request_count,
            metadata_json=payload.metadata_json,
            used_at=payload.used_at or self._utcnow(),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return LLMTokenUsageResponse.model_validate(entry)

    def record_llm_token_usage(
        self,
        *,
        account_id: int,
        provider: str,
        model_name: str,
        feature_name: str,
        actor_user_id: int | None = None,
        platform_connection_id: int | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int | None = None,
        estimated_cost: Decimal = Decimal("0"),
        request_count: int = 1,
        metadata_json: dict | None = None,
        used_at: datetime | None = None,
    ) -> LLMTokenUsage:
        entry = LLMTokenUsage(
            account_id=account_id,
            platform_connection_id=platform_connection_id,
            actor_user_id=actor_user_id,
            provider=provider.strip(),
            model_name=model_name.strip(),
            feature_name=feature_name.strip(),
            reference_type=reference_type,
            reference_id=reference_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens or (prompt_tokens + completion_tokens),
            estimated_cost=float(estimated_cost),
            request_count=request_count,
            metadata_json=metadata_json or {},
            used_at=used_at or self._utcnow(),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_llm_token_usage(
        self,
        *,
        account: Account,
        page: int,
        page_size: int,
    ) -> LLMTokenUsageListResponse:
        statement = (
            select(LLMTokenUsage)
            .where(LLMTokenUsage.account_id == account.id)
            .order_by(LLMTokenUsage.used_at.desc(), LLMTokenUsage.id.desc())
        )
        total = self.db.scalar(
            select(func.count(LLMTokenUsage.id)).where(LLMTokenUsage.account_id == account.id)
        ) or 0
        items = self.db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        return LLMTokenUsageListResponse(
            items=[LLMTokenUsageResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
