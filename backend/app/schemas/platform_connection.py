from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field, HttpUrl

from app.models.enums import ConnectionStatus, PlatformType
from app.schemas.common import APIModel, ORMModel


class WebhookConfigPayload(APIModel):
    webhook_url: HttpUrl | None = None
    webhook_secret: str | None = Field(default=None, max_length=255)
    webhook_verify_token: str | None = Field(default=None, max_length=255)
    webhook_active: bool = False


class PlatformConnectionCreateRequest(APIModel):
    platform_type: PlatformType
    name: str = Field(..., min_length=2, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    external_name: str | None = Field(default=None, max_length=255)
    access_token: str | None = Field(default=None, min_length=8, max_length=2048)
    refresh_token: str | None = Field(default=None, min_length=8, max_length=2048)
    webhook: WebhookConfigPayload | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    settings_json: dict[str, Any] = Field(default_factory=dict)


class PlatformConnectionUpdateRequest(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    external_id: str | None = Field(default=None, max_length=255)
    external_name: str | None = Field(default=None, max_length=255)
    access_token: str | None = Field(default=None, min_length=8, max_length=2048)
    refresh_token: str | None = Field(default=None, min_length=8, max_length=2048)
    webhook: WebhookConfigPayload | None = None
    metadata_json: dict[str, Any] | None = None
    settings_json: dict[str, Any] | None = None
    last_error: str | None = Field(default=None, max_length=500)


class PlatformConnectionStatusUpdateRequest(APIModel):
    status: ConnectionStatus
    last_error: str | None = Field(default=None, max_length=500)


class WebhookConfigResponse(APIModel):
    webhook_url: str | None
    webhook_active: bool
    has_secret: bool
    has_verify_token: bool


class IntegrationSummaryResponse(APIModel):
    provider: str | None = None
    connected_via: str | None = None
    sync_state: str | None = None
    token_status: str | None = None
    last_synced_at: datetime | None = None
    webhook_subscription_state: str | None = None
    page_picture_url: str | None = None
    followers_count: int | None = None
    required_permissions: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)


class PlatformConnectionResponse(ORMModel):
    id: int
    account_id: int
    platform_type: PlatformType
    name: str
    external_id: str | None
    external_name: str | None
    status: ConnectionStatus
    token_hint: str | None
    webhook: WebhookConfigResponse
    metadata_json: dict[str, Any]
    settings_json: dict[str, Any]
    last_error: str | None
    integration_summary: IntegrationSummaryResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlatformConnectionListResponse(APIModel):
    items: list[PlatformConnectionResponse]
    total: int


class FacebookOAuthStartResponse(APIModel):
    state: str
    auth_url: str
    redirect_uri: str
    scopes: list[str]


class FacebookPageCandidateResponse(APIModel):
    page_id: str
    page_name: str
    category: str | None = None
    tasks: list[str] = Field(default_factory=list)
    picture_url: str | None = None


class FacebookOAuthCompleteRequest(APIModel):
    state: str = Field(..., min_length=8, max_length=128)
    code: str = Field(..., min_length=8, max_length=2048)


class FacebookOAuthCompleteResponse(APIModel):
    state: str
    pages: list[FacebookPageCandidateResponse]


class FacebookOAuthConnectRequest(APIModel):
    state: str = Field(..., min_length=8, max_length=128)
    page_id: str = Field(..., min_length=1, max_length=255)
    connection_name: str | None = Field(default=None, min_length=2, max_length=255)
    webhook_verify_token: str | None = Field(default=None, max_length=255)
    webhook_secret: str | None = Field(default=None, max_length=255)


class FacebookManualConnectRequest(APIModel):
    page_id: str = Field(..., min_length=1, max_length=255)
    page_access_token: str = Field(..., min_length=8, max_length=2048)
    connection_name: str | None = Field(default=None, min_length=2, max_length=255)
    user_access_token: str | None = Field(default=None, min_length=8, max_length=2048)
    webhook_verify_token: str | None = Field(default=None, max_length=255)
    webhook_secret: str | None = Field(default=None, max_length=255)


class WhatsAppManualConnectRequest(APIModel):
    phone_number_id: str = Field(..., min_length=1, max_length=255)
    access_token: str = Field(..., min_length=8, max_length=2048)
    connection_name: str | None = Field(default=None, min_length=2, max_length=255)
    business_account_id: str | None = Field(default=None, max_length=255)
    display_phone_number: str | None = Field(default=None, max_length=64)
    webhook_verify_token: str | None = Field(default=None, max_length=255)
    webhook_secret: str | None = Field(default=None, max_length=255)
