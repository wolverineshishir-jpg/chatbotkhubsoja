from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.ai_agent import AIAgent
from app.models.ai_knowledge_source import AIKnowledgeSource
from app.models.ai_prompt import AIPrompt
from app.models.account import Account
from app.models.enums import PromptType
from app.models.faq_knowledge import FAQKnowledge
from app.models.platform_connection import PlatformConnection
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


class AIConfigurationService:
    def __init__(self, db: Session):
        self.db = db

    def list_agents(self, account: Account) -> list[AIAgentOverviewResponse]:
        agents = self.db.scalars(
            select(AIAgent).where(AIAgent.account_id == account.id).order_by(AIAgent.created_at.desc())
        ).all()
        return [self._to_agent_overview(agent) for agent in agents]

    def get_agent(self, account: Account, agent_id: int) -> AIAgentOverviewResponse:
        agent = self._get_agent(account.id, agent_id)
        return self._to_agent_overview(agent)

    def create_agent(self, account: Account, payload: AIAgentCreateRequest) -> AIAgentResponse:
        self._validate_connection(account.id, payload.platform_connection_id)
        agent = AIAgent(
            account_id=account.id,
            platform_connection_id=payload.platform_connection_id,
            name=payload.name,
            business_type=payload.business_type,
            status=payload.status,
            settings_json=payload.settings_json,
            behavior_json=payload.behavior_json,
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return AIAgentResponse.model_validate(agent)

    def update_agent(self, account: Account, agent_id: int, payload: AIAgentUpdateRequest) -> AIAgentResponse:
        agent = self._get_agent(account.id, agent_id)
        update_data = payload.model_dump(exclude_unset=True)
        if "platform_connection_id" in update_data:
            self._validate_connection(account.id, payload.platform_connection_id)
        for field, value in update_data.items():
            setattr(agent, field, value)
        self.db.commit()
        self.db.refresh(agent)
        return AIAgentResponse.model_validate(agent)

    def delete_agent(self, account: Account, agent_id: int) -> None:
        agent = self._get_agent(account.id, agent_id)
        self.db.delete(agent)
        self.db.commit()

    def list_prompts(self, account: Account, ai_agent_id: int | None, platform_connection_id: int | None) -> list[AIPromptResponse]:
        self._validate_connection(account.id, platform_connection_id)
        self._validate_agent(account.id, ai_agent_id)
        prompts = self.db.scalars(
            select(AIPrompt)
            .where(
                AIPrompt.account_id == account.id,
                AIPrompt.ai_agent_id == ai_agent_id,
                AIPrompt.platform_connection_id == platform_connection_id,
            )
            .order_by(AIPrompt.prompt_type.asc(), AIPrompt.version.desc())
        ).all()
        return [AIPromptResponse.model_validate(prompt) for prompt in prompts]

    def get_prompt(self, account: Account, prompt_id: int) -> AIPromptResponse:
        prompt = self._get_prompt(account.id, prompt_id)
        return AIPromptResponse.model_validate(prompt)

    def create_prompt(self, account: Account, payload: AIPromptCreateRequest) -> AIPromptResponse:
        self._validate_connection(account.id, payload.platform_connection_id)
        self._validate_agent(account.id, payload.ai_agent_id)

        version = self._next_prompt_version(
            account.id,
            payload.prompt_type,
            payload.ai_agent_id,
            payload.platform_connection_id,
        )
        prompt = AIPrompt(
            account_id=account.id,
            ai_agent_id=payload.ai_agent_id,
            platform_connection_id=payload.platform_connection_id,
            prompt_type=payload.prompt_type,
            title=payload.title,
            content=payload.content,
            version=version,
            is_active=payload.is_active,
            notes=payload.notes,
        )
        self.db.add(prompt)
        self.db.flush()
        if payload.is_active:
            self._deactivate_siblings(prompt)
        self.db.commit()
        self.db.refresh(prompt)
        return AIPromptResponse.model_validate(prompt)

    def update_prompt(self, account: Account, prompt_id: int, payload: AIPromptUpdateRequest) -> AIPromptResponse:
        prompt = self._get_prompt(account.id, prompt_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(prompt, field, value)
        if payload.is_active:
            self._deactivate_siblings(prompt)
        self.db.commit()
        self.db.refresh(prompt)
        return AIPromptResponse.model_validate(prompt)

    def delete_prompt(self, account: Account, prompt_id: int) -> None:
        prompt = self._get_prompt(account.id, prompt_id)
        self.db.delete(prompt)
        self.db.commit()

    def resolve_prompts(
        self,
        account: Account,
        ai_agent_id: int | None,
        platform_connection_id: int | None,
    ) -> list[PromptResolutionResponse]:
        self._validate_connection(account.id, platform_connection_id)
        agent = self._validate_agent(account.id, ai_agent_id)
        if agent and platform_connection_id is None:
            platform_connection_id = agent.platform_connection_id

        responses: list[PromptResolutionResponse] = []
        for prompt_type in PromptType:
            prompt, scope = self._resolve_single_prompt(account.id, prompt_type, ai_agent_id, platform_connection_id)
            responses.append(
                PromptResolutionResponse(
                    prompt_type=prompt_type,
                    source_scope=scope,
                    prompt=AIPromptResponse.model_validate(prompt) if prompt else None,
                )
            )
        return responses

    def list_knowledge_sources(self, account: Account, ai_agent_id: int | None) -> list[AIKnowledgeSourceResponse]:
        self._validate_agent(account.id, ai_agent_id)
        sources = self.db.scalars(
            select(AIKnowledgeSource)
            .where(AIKnowledgeSource.account_id == account.id)
            .where(AIKnowledgeSource.ai_agent_id == ai_agent_id if ai_agent_id is not None else True)
            .order_by(AIKnowledgeSource.created_at.desc())
        ).all()
        return [AIKnowledgeSourceResponse.model_validate(source) for source in sources]

    def create_knowledge_source(self, account: Account, payload: AIKnowledgeSourceCreateRequest) -> AIKnowledgeSourceResponse:
        self._validate_agent(account.id, payload.ai_agent_id)
        source = AIKnowledgeSource(
            account_id=account.id,
            ai_agent_id=payload.ai_agent_id,
            title=payload.title,
            source_type=payload.source_type,
            status=payload.status,
            description=payload.description,
            content_text=payload.content_text,
            metadata_json=payload.metadata_json,
            file_name=payload.file_metadata.file_name if payload.file_metadata else None,
            file_size=payload.file_metadata.file_size if payload.file_metadata else None,
            mime_type=payload.file_metadata.mime_type if payload.file_metadata else None,
            storage_key=payload.file_metadata.storage_key if payload.file_metadata else None,
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return AIKnowledgeSourceResponse.model_validate(source)

    def update_knowledge_source(
        self, account: Account, source_id: int, payload: AIKnowledgeSourceUpdateRequest
    ) -> AIKnowledgeSourceResponse:
        source = self._get_knowledge_source(account.id, source_id)
        update_data = payload.model_dump(exclude_unset=True, exclude={"file_metadata"})
        if "ai_agent_id" in update_data:
            self._validate_agent(account.id, payload.ai_agent_id)
        for field, value in update_data.items():
            setattr(source, field, value)
        if payload.file_metadata is not None:
            source.file_name = payload.file_metadata.file_name
            source.file_size = payload.file_metadata.file_size
            source.mime_type = payload.file_metadata.mime_type
            source.storage_key = payload.file_metadata.storage_key
        self.db.commit()
        self.db.refresh(source)
        return AIKnowledgeSourceResponse.model_validate(source)

    def delete_knowledge_source(self, account: Account, source_id: int) -> None:
        source = self._get_knowledge_source(account.id, source_id)
        self.db.delete(source)
        self.db.commit()

    def list_faq_entries(self, account: Account, ai_agent_id: int | None) -> list[FAQKnowledgeResponse]:
        self._validate_agent(account.id, ai_agent_id)
        faqs = self.db.scalars(
            select(FAQKnowledge)
            .where(FAQKnowledge.account_id == account.id)
            .where(FAQKnowledge.ai_agent_id == ai_agent_id if ai_agent_id is not None else True)
            .order_by(FAQKnowledge.created_at.desc())
        ).all()
        return [FAQKnowledgeResponse.model_validate(faq) for faq in faqs]

    def create_faq_entry(self, account: Account, payload: FAQKnowledgeCreateRequest) -> FAQKnowledgeResponse:
        self._validate_agent(account.id, payload.ai_agent_id)
        faq = FAQKnowledge(
            account_id=account.id,
            ai_agent_id=payload.ai_agent_id,
            question=payload.question,
            answer=payload.answer,
            tags_json=payload.tags_json,
            is_active=payload.is_active,
        )
        self.db.add(faq)
        self.db.commit()
        self.db.refresh(faq)
        return FAQKnowledgeResponse.model_validate(faq)

    def update_faq_entry(self, account: Account, faq_id: int, payload: FAQKnowledgeUpdateRequest) -> FAQKnowledgeResponse:
        faq = self._get_faq(account.id, faq_id)
        update_data = payload.model_dump(exclude_unset=True)
        if "ai_agent_id" in update_data:
            self._validate_agent(account.id, payload.ai_agent_id)
        for field, value in update_data.items():
            setattr(faq, field, value)
        self.db.commit()
        self.db.refresh(faq)
        return FAQKnowledgeResponse.model_validate(faq)

    def delete_faq_entry(self, account: Account, faq_id: int) -> None:
        faq = self._get_faq(account.id, faq_id)
        self.db.delete(faq)
        self.db.commit()

    def _to_agent_overview(self, agent: AIAgent) -> AIAgentOverviewResponse:
        prompt_count = self.db.scalar(select(func.count(AIPrompt.id)).where(AIPrompt.ai_agent_id == agent.id)) or 0
        knowledge_count = self.db.scalar(
            select(func.count(AIKnowledgeSource.id)).where(AIKnowledgeSource.ai_agent_id == agent.id)
        ) or 0
        faq_count = self.db.scalar(select(func.count(FAQKnowledge.id)).where(FAQKnowledge.ai_agent_id == agent.id)) or 0
        return AIAgentOverviewResponse(
            **AIAgentResponse.model_validate(agent).model_dump(),
            prompt_count=prompt_count,
            knowledge_source_count=knowledge_count,
            faq_count=faq_count,
        )

    def _resolve_single_prompt(
        self, account_id: int, prompt_type: PromptType, ai_agent_id: int | None, platform_connection_id: int | None
    ) -> tuple[AIPrompt | None, str]:
        lookups = [
            ("agent-specific", and_(AIPrompt.ai_agent_id == ai_agent_id, AIPrompt.is_active.is_(True))),
            (
                "connection-specific",
                and_(
                    AIPrompt.ai_agent_id.is_(None),
                    AIPrompt.platform_connection_id == platform_connection_id,
                    AIPrompt.is_active.is_(True),
                ),
            ),
            (
                "account-default",
                and_(
                    AIPrompt.ai_agent_id.is_(None),
                    AIPrompt.platform_connection_id.is_(None),
                    AIPrompt.is_active.is_(True),
                ),
            ),
        ]

        for scope, clause in lookups:
            if scope == "agent-specific" and ai_agent_id is None:
                continue
            if scope == "connection-specific" and platform_connection_id is None:
                continue
            prompt = self.db.scalar(
                select(AIPrompt)
                .where(AIPrompt.account_id == account_id, AIPrompt.prompt_type == prompt_type, clause)
                .order_by(AIPrompt.version.desc(), AIPrompt.updated_at.desc())
            )
            if prompt:
                return prompt, scope
        return None, "none"

    def _next_prompt_version(
        self,
        account_id: int,
        prompt_type: PromptType,
        ai_agent_id: int | None,
        platform_connection_id: int | None,
    ) -> int:
        version = self.db.scalar(
            select(func.max(AIPrompt.version)).where(
                AIPrompt.account_id == account_id,
                AIPrompt.prompt_type == prompt_type,
                AIPrompt.ai_agent_id == ai_agent_id,
                AIPrompt.platform_connection_id == platform_connection_id,
            )
        )
        return (version or 0) + 1

    def _deactivate_siblings(self, prompt: AIPrompt) -> None:
        siblings = self.db.scalars(
            select(AIPrompt).where(
                AIPrompt.account_id == prompt.account_id,
                AIPrompt.prompt_type == prompt.prompt_type,
                AIPrompt.ai_agent_id == prompt.ai_agent_id,
                AIPrompt.platform_connection_id == prompt.platform_connection_id,
                AIPrompt.id != prompt.id,
                AIPrompt.is_active.is_(True),
            )
        ).all()
        for sibling in siblings:
            sibling.is_active = False

    def _validate_connection(self, account_id: int, connection_id: int | None) -> PlatformConnection | None:
        if connection_id is None:
            return None
        connection = self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.account_id == account_id, PlatformConnection.id == connection_id
            )
        )
        if not connection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found for account.")
        return connection

    def _validate_agent(self, account_id: int, agent_id: int | None) -> AIAgent | None:
        if agent_id is None:
            return None
        return self._get_agent(account_id, agent_id)

    def _get_agent(self, account_id: int, agent_id: int) -> AIAgent:
        agent = self.db.scalar(select(AIAgent).where(AIAgent.account_id == account_id, AIAgent.id == agent_id))
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI agent not found.")
        return agent

    def _get_prompt(self, account_id: int, prompt_id: int) -> AIPrompt:
        prompt = self.db.scalar(select(AIPrompt).where(AIPrompt.account_id == account_id, AIPrompt.id == prompt_id))
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI prompt not found.")
        return prompt

    def _get_knowledge_source(self, account_id: int, source_id: int) -> AIKnowledgeSource:
        source = self.db.scalar(
            select(AIKnowledgeSource).where(AIKnowledgeSource.account_id == account_id, AIKnowledgeSource.id == source_id)
        )
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found.")
        return source

    def _get_faq(self, account_id: int, faq_id: int) -> FAQKnowledge:
        faq = self.db.scalar(select(FAQKnowledge).where(FAQKnowledge.account_id == account_id, FAQKnowledge.id == faq_id))
        if not faq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ entry not found.")
        return faq
