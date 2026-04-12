from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import PlatformType, WebhookEventStatus


class WebhookAckResponse(BaseModel):
    event_id: int
    status: WebhookEventStatus
    queued: bool


class WebhookVerifyResponse(BaseModel):
    mode: str | None = None
    challenge: str | None = None
    verified: bool


class WebhookEventSummaryResponse(BaseModel):
    id: int
    platform_type: PlatformType
    event_type: str
    status: WebhookEventStatus
    received_at: datetime
    processed_at: datetime | None
    attempts: int
    delivery_id: str | None
    error_message: str | None
    metadata_json: dict = Field(default_factory=dict)
