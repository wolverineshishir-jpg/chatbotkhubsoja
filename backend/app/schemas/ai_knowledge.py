from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import KnowledgeSourceStatus, KnowledgeSourceType
from app.schemas.common import ORMModel


class FileMetadataPayload(BaseModel):
    file_name: str | None = Field(default=None, max_length=255)
    file_size: int | None = Field(default=None, ge=0)
    mime_type: str | None = Field(default=None, max_length=255)
    storage_key: str | None = Field(default=None, max_length=500)


class AIKnowledgeSourceCreateRequest(BaseModel):
    ai_agent_id: int | None = None
    title: str = Field(..., min_length=2, max_length=255)
    source_type: KnowledgeSourceType
    status: KnowledgeSourceStatus = KnowledgeSourceStatus.DRAFT
    description: str | None = Field(default=None, max_length=500)
    content_text: str | None = None
    file_metadata: FileMetadataPayload | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AIKnowledgeSourceUpdateRequest(BaseModel):
    ai_agent_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    source_type: KnowledgeSourceType | None = None
    status: KnowledgeSourceStatus | None = None
    description: str | None = Field(default=None, max_length=500)
    content_text: str | None = None
    file_metadata: FileMetadataPayload | None = None
    metadata_json: dict[str, Any] | None = None


class AIKnowledgeSourceResponse(ORMModel):
    id: int
    account_id: int
    ai_agent_id: int | None
    title: str
    source_type: KnowledgeSourceType
    status: KnowledgeSourceStatus
    description: str | None
    content_text: str | None
    file_name: str | None
    file_size: int | None
    mime_type: str | None
    storage_key: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime
