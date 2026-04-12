from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import AutomationActionType, AutomationTriggerType, AutomationWorkflowStatus
from app.schemas.common import ORMModel


class AutomationTriggerFilters(BaseModel):
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    customer_contains: str | None = Field(default=None, max_length=255)

    @field_validator("include_keywords", "exclude_keywords")
    @classmethod
    def normalize_keywords(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            keyword = item.strip()
            if not keyword:
                continue
            lowered = keyword.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            cleaned.append(keyword)
        return cleaned


class AutomationActionConfig(BaseModel):
    instructions: str | None = Field(default=None, max_length=2000)
    send_now: bool = False
    title_hint: str | None = Field(default=None, max_length=255)


class AutomationWorkflowCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    status: AutomationWorkflowStatus = AutomationWorkflowStatus.DRAFT
    trigger_type: AutomationTriggerType
    action_type: AutomationActionType
    platform_connection_id: int | None = None
    ai_agent_id: int | None = None
    delay_seconds: int = Field(default=0, ge=0, le=86400)
    trigger_filters: AutomationTriggerFilters = Field(default_factory=AutomationTriggerFilters)
    action_config: AutomationActionConfig = Field(default_factory=AutomationActionConfig)
    schedule_timezone: str | None = Field(default=None, max_length=64)
    schedule_local_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_action_for_trigger(self.trigger_type, self.action_type)
        _validate_schedule_fields(self.trigger_type, self.schedule_timezone, self.schedule_local_time)
        return self


class AutomationWorkflowUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    status: AutomationWorkflowStatus | None = None
    trigger_type: AutomationTriggerType | None = None
    action_type: AutomationActionType | None = None
    platform_connection_id: int | None = None
    ai_agent_id: int | None = None
    delay_seconds: int | None = Field(default=None, ge=0, le=86400)
    trigger_filters: AutomationTriggerFilters | None = None
    action_config: AutomationActionConfig | None = None
    schedule_timezone: str | None = Field(default=None, max_length=64)
    schedule_local_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")


class AutomationWorkflowResponse(ORMModel):
    id: int
    account_id: int
    platform_connection_id: int | None
    ai_agent_id: int | None
    name: str
    description: str | None
    status: AutomationWorkflowStatus
    trigger_type: AutomationTriggerType
    action_type: AutomationActionType
    delay_seconds: int
    trigger_filters_json: dict[str, Any]
    action_config_json: dict[str, Any]
    schedule_timezone: str | None
    schedule_local_time: str | None
    next_run_at: datetime | None
    last_triggered_at: datetime | None
    last_result_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AutomationWorkflowListResponse(BaseModel):
    items: list[AutomationWorkflowResponse]
    total: int


class AutomationWorkflowRunResponse(BaseModel):
    workflow: AutomationWorkflowResponse
    sync_job_id: int


def _validate_action_for_trigger(trigger_type: AutomationTriggerType, action_type: AutomationActionType) -> None:
    valid_pairs: dict[AutomationTriggerType, set[AutomationActionType]] = {
        AutomationTriggerType.INBOX_MESSAGE_RECEIVED: {AutomationActionType.GENERATE_INBOX_REPLY},
        AutomationTriggerType.FACEBOOK_COMMENT_CREATED: {AutomationActionType.GENERATE_COMMENT_REPLY},
        AutomationTriggerType.SCHEDULED_DAILY: {AutomationActionType.GENERATE_POST_DRAFT},
    }
    if action_type not in valid_pairs[trigger_type]:
        raise ValueError("Selected action is not compatible with this trigger.")


def _validate_schedule_fields(
    trigger_type: AutomationTriggerType,
    schedule_timezone: str | None,
    schedule_local_time: str | None,
) -> None:
    if trigger_type == AutomationTriggerType.SCHEDULED_DAILY:
        if not schedule_timezone or not schedule_local_time:
            raise ValueError("Scheduled daily workflows require schedule_timezone and schedule_local_time.")
        return
    if schedule_timezone or schedule_local_time:
        raise ValueError("Schedule fields are only supported for scheduled daily workflows.")
