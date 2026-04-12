from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps.auth import require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.membership import Membership
from app.schemas.ai_agent import AIAgentCreateRequest, AIAgentOverviewResponse, AIAgentResponse, AIAgentUpdateRequest
from app.schemas.ai_knowledge import (
    AIKnowledgeSourceCreateRequest,
    AIKnowledgeSourceResponse,
    AIKnowledgeSourceUpdateRequest,
)
from app.schemas.ai_prompt import (
    AIPromptCreateRequest,
    AIPromptResponse,
    AIPromptUpdateRequest,
    PromptResolutionResponse,
)
from app.schemas.faq import FAQKnowledgeCreateRequest, FAQKnowledgeResponse, FAQKnowledgeUpdateRequest
from app.services.ai_configuration_service import AIConfigurationService

router = APIRouter()


@router.get("/agents", response_model=list[AIAgentOverviewResponse])
def list_ai_agents(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:read"))],
    db: Session = Depends(get_db),
) -> list[AIAgentOverviewResponse]:
    account, _ = context
    return AIConfigurationService(db).list_agents(account)


@router.post("/agents", response_model=AIAgentResponse, status_code=status.HTTP_201_CREATED)
def create_ai_agent(
    payload: AIAgentCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> AIAgentResponse:
    account, _ = context
    return AIConfigurationService(db).create_agent(account, payload)


@router.get("/agents/{agent_id}", response_model=AIAgentOverviewResponse)
def get_ai_agent(
    agent_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:read"))],
    db: Session = Depends(get_db),
) -> AIAgentOverviewResponse:
    account, _ = context
    return AIConfigurationService(db).get_agent(account, agent_id)


@router.put("/agents/{agent_id}", response_model=AIAgentResponse)
def update_ai_agent(
    agent_id: int,
    payload: AIAgentUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> AIAgentResponse:
    account, _ = context
    return AIConfigurationService(db).update_agent(account, agent_id, payload)


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_ai_agent(
    agent_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> Response:
    account, _ = context
    AIConfigurationService(db).delete_agent(account, agent_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/prompts", response_model=list[AIPromptResponse])
def list_ai_prompts(
    ai_agent_id: int | None = Query(default=None),
    platform_connection_id: int | None = Query(default=None),
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:read"))] = None,
    db: Session = Depends(get_db),
) -> list[AIPromptResponse]:
    account, _ = context
    return AIConfigurationService(db).list_prompts(account, ai_agent_id, platform_connection_id)


@router.post("/prompts", response_model=AIPromptResponse, status_code=status.HTTP_201_CREATED)
def create_ai_prompt(
    payload: AIPromptCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> AIPromptResponse:
    account, _ = context
    return AIConfigurationService(db).create_prompt(account, payload)


@router.get("/prompts/{prompt_id}", response_model=AIPromptResponse)
def get_ai_prompt(
    prompt_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:read"))],
    db: Session = Depends(get_db),
) -> AIPromptResponse:
    account, _ = context
    return AIConfigurationService(db).get_prompt(account, prompt_id)


@router.put("/prompts/{prompt_id}", response_model=AIPromptResponse)
def update_ai_prompt(
    prompt_id: int,
    payload: AIPromptUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> AIPromptResponse:
    account, _ = context
    return AIConfigurationService(db).update_prompt(account, prompt_id, payload)


@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_ai_prompt(
    prompt_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> Response:
    account, _ = context
    AIConfigurationService(db).delete_prompt(account, prompt_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/prompts/resolve/current", response_model=list[PromptResolutionResponse])
def resolve_ai_prompts(
    ai_agent_id: int | None = Query(default=None),
    platform_connection_id: int | None = Query(default=None),
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:read"))] = None,
    db: Session = Depends(get_db),
) -> list[PromptResolutionResponse]:
    account, _ = context
    return AIConfigurationService(db).resolve_prompts(account, ai_agent_id, platform_connection_id)


@router.get("/knowledge-sources", response_model=list[AIKnowledgeSourceResponse])
def list_knowledge_sources(
    ai_agent_id: int | None = Query(default=None),
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:read"))] = None,
    db: Session = Depends(get_db),
) -> list[AIKnowledgeSourceResponse]:
    account, _ = context
    return AIConfigurationService(db).list_knowledge_sources(account, ai_agent_id)


@router.post("/knowledge-sources", response_model=AIKnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_source(
    payload: AIKnowledgeSourceCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> AIKnowledgeSourceResponse:
    account, _ = context
    return AIConfigurationService(db).create_knowledge_source(account, payload)


@router.put("/knowledge-sources/{source_id}", response_model=AIKnowledgeSourceResponse)
def update_knowledge_source(
    source_id: int,
    payload: AIKnowledgeSourceUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> AIKnowledgeSourceResponse:
    account, _ = context
    return AIConfigurationService(db).update_knowledge_source(account, source_id, payload)


@router.delete("/knowledge-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_knowledge_source(
    source_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> Response:
    account, _ = context
    AIConfigurationService(db).delete_knowledge_source(account, source_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/faq", response_model=list[FAQKnowledgeResponse])
def list_faq_entries(
    ai_agent_id: int | None = Query(default=None),
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:read"))] = None,
    db: Session = Depends(get_db),
) -> list[FAQKnowledgeResponse]:
    account, _ = context
    return AIConfigurationService(db).list_faq_entries(account, ai_agent_id)


@router.post("/faq", response_model=FAQKnowledgeResponse, status_code=status.HTTP_201_CREATED)
def create_faq_entry(
    payload: FAQKnowledgeCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> FAQKnowledgeResponse:
    account, _ = context
    return AIConfigurationService(db).create_faq_entry(account, payload)


@router.put("/faq/{faq_id}", response_model=FAQKnowledgeResponse)
def update_faq_entry(
    faq_id: int,
    payload: FAQKnowledgeUpdateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> FAQKnowledgeResponse:
    account, _ = context
    return AIConfigurationService(db).update_faq_entry(account, faq_id, payload)


@router.delete("/faq/{faq_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_faq_entry(
    faq_id: int,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("ai:manage"))],
    db: Session = Depends(get_db),
) -> Response:
    account, _ = context
    AIConfigurationService(db).delete_faq_entry(account, faq_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
