from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import AIAgentStatus
from app.schemas.common import ORMModel


class AIAgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    business_type: str | None = Field(default=None, max_length=255)
    platform_connection_id: int | None = None
    settings_json: dict[str, Any] = Field(default_factory=dict)
    behavior_json: dict[str, Any] = Field(default_factory=dict)
    status: AIAgentStatus = AIAgentStatus.DRAFT


class AIAgentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    business_type: str | None = Field(default=None, max_length=255)
    platform_connection_id: int | None = None
    settings_json: dict[str, Any] | None = None
    behavior_json: dict[str, Any] | None = None
    status: AIAgentStatus | None = None


class AIAgentResponse(ORMModel):
    id: int
    account_id: int
    platform_connection_id: int | None
    name: str
    business_type: str | None
    status: AIAgentStatus
    settings_json: dict[str, Any]
    behavior_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AIAgentOverviewResponse(AIAgentResponse):
    prompt_count: int
    knowledge_source_count: int
    faq_count: int
