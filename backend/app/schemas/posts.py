from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import PlatformType, PostGeneratedBy, PostStatus
from app.schemas.common import ORMModel


class SocialPostCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str = Field(..., min_length=1, max_length=5000)
    media_urls: list[str] = Field(default_factory=list)
    platform_connection_id: int | None = None
    ai_agent_id: int | None = None
    ai_prompt_id: int | None = None
    generated_by: PostGeneratedBy = PostGeneratedBy.HUMAN_ADMIN
    is_llm_generated: bool = False
    requires_approval: bool = False
    scheduled_for: datetime | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("media_urls")
    @classmethod
    def validate_media_urls(cls, value: list[str]) -> list[str]:
        if len(value) > 10:
            raise ValueError("A post can have at most 10 media URLs.")
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_generated_flags(self):
        if self.generated_by == PostGeneratedBy.LLM_BOT and not self.is_llm_generated:
            raise ValueError("LLM-generated posts must set is_llm_generated to true.")
        return self


class SocialPostUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    media_urls: list[str] | None = None
    platform_connection_id: int | None = None
    ai_agent_id: int | None = None
    ai_prompt_id: int | None = None
    generated_by: PostGeneratedBy | None = None
    is_llm_generated: bool | None = None
    requires_approval: bool | None = None
    metadata_json: dict[str, Any] | None = None

    @field_validator("media_urls")
    @classmethod
    def validate_media_urls(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if len(value) > 10:
            raise ValueError("A post can have at most 10 media URLs.")
        return [item.strip() for item in value if item.strip()]


class PostApprovalRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class PostRejectRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=500)


class PostScheduleRequest(BaseModel):
    scheduled_for: datetime


class SocialPostResponse(ORMModel):
    id: int
    account_id: int
    platform_connection_id: int | None
    ai_agent_id: int | None
    ai_prompt_id: int | None
    created_by_user_id: int | None
    approved_by_user_id: int | None
    rejected_by_user_id: int | None
    platform_type: PlatformType
    status: PostStatus
    generated_by: PostGeneratedBy
    title: str | None
    content: str
    media_urls: list[str]
    external_post_id: str | None
    is_llm_generated: bool
    requires_approval: bool
    scheduled_for: datetime | None
    published_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None
    rejection_reason: str | None
    last_error: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SocialPostListResponse(BaseModel):
    items: list[SocialPostResponse]
    total: int
    page: int
    page_size: int
