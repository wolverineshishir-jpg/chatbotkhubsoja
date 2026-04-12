from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import PromptType
from app.schemas.common import ORMModel


class AIPromptCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=1)
    prompt_type: PromptType
    ai_agent_id: int | None = None
    platform_connection_id: int | None = None
    is_active: bool = True
    notes: str | None = Field(default=None, max_length=500)


class AIPromptUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None
    notes: str | None = Field(default=None, max_length=500)


class PromptActivationRequest(BaseModel):
    is_active: bool = True


class PromptResolveQuery(BaseModel):
    ai_agent_id: int | None = None
    platform_connection_id: int | None = None


class AIPromptResponse(ORMModel):
    id: int
    account_id: int
    ai_agent_id: int | None
    platform_connection_id: int | None
    prompt_type: PromptType
    title: str
    content: str
    version: int
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PromptResolutionResponse(BaseModel):
    prompt_type: PromptType
    source_scope: str
    prompt: AIPromptResponse | None
