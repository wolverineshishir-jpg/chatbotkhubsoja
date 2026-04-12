from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.ai.providers.base import LLMGenerationResult

try:
    from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError
except ImportError:  # pragma: no cover - handled at runtime if dependency is missing
    APIConnectionError = APIStatusError = APITimeoutError = RateLimitError = None
    OpenAI = None


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = self._build_client()

    def _build_client(self):
        api_key = self.settings.openai_api_key.get_secret_value().strip()
        if not api_key:
            return None
        if OpenAI is None:
            return None

        client_kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": self.settings.openai_timeout_seconds,
        }
        if self.settings.openai_base_url:
            client_kwargs["base_url"] = self.settings.openai_base_url
        if self.settings.openai_organization_id:
            client_kwargs["organization"] = self.settings.openai_organization_id
        if self.settings.openai_project_id:
            client_kwargs["project"] = self.settings.openai_project_id
        return OpenAI(**client_kwargs)

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int = 512,
        temperature: float = 0.2,
        model_name: str | None = None,
    ) -> LLMGenerationResult:
        del temperature

        if OpenAI is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI SDK is not installed. Add the 'openai' package to enable this provider.",
            )

        if self._client is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI provider is not configured. Set OPENAI_API_KEY to enable it.",
            )

        resolved_model_name = (model_name or self.settings.llm_default_model).strip()
        if not resolved_model_name or resolved_model_name == "internal-reply-model-v1":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI provider is selected but no OpenAI model is configured. Set LLM_DEFAULT_MODEL.",
            )

        try:
            response = self._client.responses.create(
                model=resolved_model_name,
                instructions=system_prompt,
                input=user_prompt,
                max_output_tokens=max_output_tokens,
            )
        except RateLimitError as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OpenAI rate limit reached. Please retry shortly.",
            ) from exc
        except APITimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="OpenAI request timed out.",
            ) from exc
        except APIConnectionError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to reach OpenAI.",
            ) from exc
        except APIStatusError as exc:
            detail = getattr(exc, "message", None) or "OpenAI request failed."
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=detail,
            ) from exc

        content = (getattr(response, "output_text", None) or "").strip()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenAI returned no text output.",
            )

        usage = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "output_tokens", 0) or 0)

        return LLMGenerationResult(
            content=content,
            provider=self.provider_name,
            model_name=resolved_model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
