from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CommentReplyStatus, CommentStatus, PlatformType, SenderType
from app.schemas.common import ORMModel


class CommentAssigneeResponse(BaseModel):
    user_id: int
    full_name: str | None
    email: str


class FacebookCommentReplyResponse(ORMModel):
    id: int
    account_id: int
    comment_id: int
    created_by_user_id: int | None
    sender_type: SenderType
    reply_status: CommentReplyStatus
    content: str
    external_reply_id: str | None
    error_message: str | None
    sent_at: datetime | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FacebookCommentSummaryResponse(ORMModel):
    id: int
    account_id: int
    platform_connection_id: int | None
    platform_type: PlatformType
    status: CommentStatus
    post_external_id: str
    post_title: str | None
    post_url: str | None
    external_comment_id: str
    parent_external_comment_id: str | None
    commenter_external_id: str
    commenter_name: str | None
    commenter_avatar_url: str | None
    comment_text: str
    ai_draft_reply: str | None
    flagged_reason: str | None
    moderation_notes: str | None
    commented_at: datetime | None
    last_replied_at: datetime | None
    metadata_json: dict[str, Any]
    assigned_to: CommentAssigneeResponse | None = None
    reply_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FacebookCommentDetailResponse(FacebookCommentSummaryResponse):
    replies: list[FacebookCommentReplyResponse] = Field(default_factory=list)


class FacebookCommentListResponse(BaseModel):
    items: list[FacebookCommentSummaryResponse]
    total: int
    page: int
    page_size: int


class FacebookCommentStatusUpdateRequest(BaseModel):
    status: CommentStatus
    assignee_user_id: int | None = None
    flagged_reason: str | None = Field(default=None, max_length=500)
    moderation_notes: str | None = Field(default=None, max_length=1000)
    metadata_json: dict[str, Any] | None = None


class FacebookCommentReplyCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    sender_type: SenderType
    send_now: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)
