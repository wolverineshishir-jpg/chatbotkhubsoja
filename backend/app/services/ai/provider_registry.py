from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.ai.providers.base import LLMProvider
from app.services.ai.providers.internal_provider import InternalLLMProvider
from app.services.ai.providers.openai_provider import OpenAIProvider


class LLMProviderRegistry:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._providers: dict[str, LLMProvider] = {
            "internal": InternalLLMProvider(),
            "openai": OpenAIProvider(),
        }

    def resolve(self, provider_name: str | None = None) -> LLMProvider:
        key = (provider_name or self.settings.llm_default_provider or "internal").strip().lower()
        provider = self._providers.get(key)
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown LLM provider '{key}'.",
            )
        return provider
