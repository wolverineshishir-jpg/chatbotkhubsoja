from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class FAQKnowledgeCreateRequest(BaseModel):
    ai_agent_id: int | None = None
    question: str = Field(..., min_length=2, max_length=500)
    answer: str = Field(..., min_length=1)
    tags_json: list[str] = Field(default_factory=list)
    is_active: bool = True


class FAQKnowledgeUpdateRequest(BaseModel):
    ai_agent_id: int | None = None
    question: str | None = Field(default=None, min_length=2, max_length=500)
    answer: str | None = Field(default=None, min_length=1)
    tags_json: list[str] | None = None
    is_active: bool | None = None


class FAQKnowledgeResponse(ORMModel):
    id: int
    account_id: int
    ai_agent_id: int | None
    question: str
    answer: str
    tags_json: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
