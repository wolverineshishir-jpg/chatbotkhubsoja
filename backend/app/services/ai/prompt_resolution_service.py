from __future__ import annotations

from sqlalchemy import select

from app.models.ai_prompt import AIPrompt
from app.models.account import Account
from app.models.enums import PromptType
from app.services.ai_configuration_service import AIConfigurationService


class PromptResolutionService:
    def __init__(self, ai_config: AIConfigurationService):
        self.ai_config = ai_config

    def resolve_prompt(
        self,
        *,
        account: Account,
        prompt_type: PromptType,
        ai_agent_id: int | None = None,
        platform_connection_id: int | None = None,
    ) -> tuple[AIPrompt | None, str]:
        resolutions = self.ai_config.resolve_prompts(
            account=account,
            ai_agent_id=ai_agent_id,
            platform_connection_id=platform_connection_id,
        )
        match = next((item for item in resolutions if item.prompt_type == prompt_type), None)
        if not match:
            return None, "none"
        if not match.prompt:
            return None, match.source_scope
        prompt = self.ai_config.db.scalar(
            select(AIPrompt).where(AIPrompt.account_id == account.id, AIPrompt.id == match.prompt.id)
        )
        return prompt, match.source_scope
