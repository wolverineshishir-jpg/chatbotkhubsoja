from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ConversationStatus,
    MessageDeliveryStatus,
    MessageDirection,
    PlatformType,
    SenderType,
)
from app.schemas.common import ORMModel


class ConversationAssigneeResponse(BaseModel):
    user_id: int
    full_name: str | None
    email: str


class ConversationSummaryResponse(ORMModel):
    id: int
    account_id: int
    platform_connection_id: int | None
    platform_type: PlatformType
    status: ConversationStatus
    external_thread_id: str | None
    customer_external_id: str
    customer_name: str | None
    customer_avatar_url: str | None
    customer_phone: str | None
    customer_email: str | None
    subject: str | None
    latest_message_preview: str | None
    latest_message_at: datetime | None
    paused_until: datetime | None
    resolved_at: datetime | None
    last_inbound_at: datetime | None
    unread_count: int = 0
    assigned_to: ConversationAssigneeResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(ORMModel):
    id: int
    account_id: int
    conversation_id: int
    created_by_user_id: int | None
    sender_type: SenderType
    direction: MessageDirection
    delivery_status: MessageDeliveryStatus
    sender_name: str | None
    sender_external_id: str | None
    external_message_id: str | None
    content: str
    error_message: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationSummaryResponse):
    messages_total: int = 0
    messages: list[MessageResponse] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    items: list[ConversationSummaryResponse]
    total: int
    page: int
    page_size: int


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    page: int
    page_size: int


class ConversationAssignRequest(BaseModel):
    assignee_user_id: int | None = None


class ConversationStatusUpdateRequest(BaseModel):
    status: ConversationStatus
    paused_until: datetime | None = None


class SendReplyRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    sender_type: SenderType = SenderType.HUMAN_ADMIN
