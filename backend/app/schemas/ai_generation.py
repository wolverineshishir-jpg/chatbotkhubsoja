from pydantic import BaseModel, Field


class InboxReplyGenerationRequest(BaseModel):
    conversation_id: int
    ai_agent_id: int | None = None
    platform_connection_id: int | None = None
    instructions: str | None = Field(default=None, max_length=4000)
    send_now: bool = False
    persist_draft: bool = True


class CommentReplyGenerationRequest(BaseModel):
    comment_id: int
    ai_agent_id: int | None = None
    instructions: str | None = Field(default=None, max_length=4000)
    send_now: bool = False
    persist_draft: bool = True


class PostGenerationRequest(BaseModel):
    platform_connection_id: int | None = None
    ai_agent_id: int | None = None
    post_id: int | None = None
    title_hint: str | None = Field(default=None, max_length=255)
    instructions: str | None = Field(default=None, max_length=4000)
    persist_draft: bool = True


class AIGenerationResponse(BaseModel):
    content: str
    requires_approval: bool
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_id: int | None
    prompt_scope: str
    ai_agent_id: int | None
    platform_connection_id: int | None
    draft_reference_type: str | None
    draft_object_id: int | None
