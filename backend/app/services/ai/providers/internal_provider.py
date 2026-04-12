from __future__ import annotations

from app.core.config import get_settings
from app.services.ai.providers.base import LLMGenerationResult


class InternalLLMProvider:
    provider_name = "internal"

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int = 512,
        temperature: float = 0.2,
        model_name: str | None = None,
    ) -> LLMGenerationResult:
        del temperature  # deterministic placeholder provider for local/dev environments
        guidance = user_prompt.strip().splitlines()
        topic = guidance[0] if guidance else "customer inquiry"
        response = (
            "Thanks for reaching out. "
            f"Here is a helpful response draft based on your context: {topic[:280]}"
        ).strip()
        words = response.split()
        if len(words) > max_output_tokens:
            response = " ".join(words[:max_output_tokens])
        prompt_tokens = max((len(system_prompt.split()) + len(user_prompt.split())), 1)
        completion_tokens = max(len(response.split()), 1)
        return LLMGenerationResult(
            content=response,
            provider=self.provider_name,
            model_name=(model_name or self.settings.llm_default_model).strip(),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
