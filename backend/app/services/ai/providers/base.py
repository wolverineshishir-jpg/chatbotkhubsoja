from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class LLMGenerationResult:
    content: str
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LLMProvider(Protocol):
    provider_name: str

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int = 512,
        temperature: float = 0.2,
        model_name: str | None = None,
    ) -> LLMGenerationResult:
        ...
