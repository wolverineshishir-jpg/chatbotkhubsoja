from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ActionUsageType, AuditActionType, AuditResourceType, PlatformType
from app.schemas.common import ORMModel


class ActionUsageLogCreateRequest(BaseModel):
    action_type: ActionUsageType
    platform_connection_id: int | None = None
    platform_type: PlatformType | None = None
    reference_type: str | None = Field(default=None, max_length=100)
    reference_id: str | None = Field(default=None, max_length=255)
    quantity: int = Field(default=1, ge=1)
    tokens_consumed: int = Field(default=0, ge=0)
    estimated_cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    occurred_at: datetime | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ActionUsageLogResponse(ORMModel):
    id: int
    account_id: int
    platform_connection_id: int | None
    actor_user_id: int | None
    action_type: ActionUsageType
    platform_type: PlatformType | None
    reference_type: str | None
    reference_id: str | None
    quantity: int
    tokens_consumed: int
    estimated_cost: Decimal
    occurred_at: datetime
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ActionUsageLogListResponse(BaseModel):
    items: list[ActionUsageLogResponse]
    total: int
    page: int
    page_size: int


class LLMTokenUsageCreateRequest(BaseModel):
    platform_connection_id: int | None = None
    provider: str = Field(..., min_length=2, max_length=100)
    model_name: str = Field(..., min_length=2, max_length=100)
    feature_name: str = Field(..., min_length=2, max_length=100)
    reference_type: str | None = Field(default=None, max_length=100)
    reference_id: str | None = Field(default=None, max_length=255)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    request_count: int = Field(default=1, ge=1)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    used_at: datetime | None = None

    @model_validator(mode="after")
    def derive_total_tokens(self):
        if self.total_tokens is None:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        return self


class LLMTokenUsageResponse(ORMModel):
    id: int
    account_id: int
    platform_connection_id: int | None
    actor_user_id: int | None
    provider: str
    model_name: str
    feature_name: str
    reference_type: str | None
    reference_id: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: Decimal
    request_count: int
    used_at: datetime
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class LLMTokenUsageListResponse(BaseModel):
    items: list[LLMTokenUsageResponse]
    total: int
    page: int
    page_size: int


class AuditLogResponse(ORMModel):
    id: int
    account_id: int
    actor_user_id: int | None
    action_type: AuditActionType
    resource_type: AuditResourceType
    resource_id: str | None
    description: str
    ip_address: str | None
    user_agent: str | None
    occurred_at: datetime
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
