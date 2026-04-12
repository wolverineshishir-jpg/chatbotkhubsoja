from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.ai.providers.base import LLMGenerationResult, LLMProvider


@dataclass(slots=True)
class StructuredReplyCandidate:
    reply_text: str
    safe_to_send: bool
    confidence: float
    escalate_to_mini: bool
    raw_payload: dict[str, Any]


@dataclass(slots=True)
class ReplyRoutingOutcome:
    generation: LLMGenerationResult
    requires_human_review: bool
    metadata: dict[str, Any]


class ReplyRoutingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_reply(
        self,
        *,
        provider: LLMProvider,
        system_prompt: str,
        user_prompt: str,
        source_text: str,
        instructions: str,
        max_output_tokens: int,
        max_reply_chars: int,
    ) -> ReplyRoutingOutcome:
        if provider.provider_name != "openai":
            generation = provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_output_tokens=max_output_tokens,
            )
            return ReplyRoutingOutcome(
                generation=generation,
                requires_human_review=False,
                metadata={"routing": "single_model", "selected_model": generation.model_name},
            )

        structured_system_prompt = self._build_structured_system_prompt(system_prompt, max_reply_chars=max_reply_chars)
        structured_user_prompt = self._build_structured_user_prompt(user_prompt)

        primary_generation = provider.generate(
            system_prompt=structured_system_prompt,
            user_prompt=structured_user_prompt,
            max_output_tokens=max_output_tokens,
            model_name=self.settings.openai_reply_primary_model,
        )
        primary_candidate, primary_errors = self._parse_candidate(primary_generation.content, max_reply_chars=max_reply_chars)
        source_reasons = self._source_escalation_reasons(source_text=source_text, instructions=instructions)
        candidate_reasons = self._candidate_escalation_reasons(primary_candidate, primary_errors)
        escalation_reasons = source_reasons + candidate_reasons

        if not escalation_reasons and primary_candidate is not None:
            return ReplyRoutingOutcome(
                generation=self._with_content(primary_generation, primary_candidate.reply_text),
                requires_human_review=False,
                metadata={
                    "routing": "primary_only",
                    "selected_model": primary_generation.model_name,
                    "escalation_reasons": [],
                },
            )

        fallback_generation = provider.generate(
            system_prompt=structured_system_prompt,
            user_prompt=structured_user_prompt,
            max_output_tokens=max_output_tokens,
            model_name=self.settings.openai_reply_fallback_model,
        )
        fallback_candidate, fallback_errors = self._parse_candidate(fallback_generation.content, max_reply_chars=max_reply_chars)
        if fallback_candidate is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Fallback reply validation failed: {', '.join(fallback_errors)}.",
            )
        if not fallback_candidate.safe_to_send:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Fallback reply requires human review and was not auto-approved for sending.",
            )

        combined_generation = self._combine_generations(
            primary_generation,
            self._with_content(fallback_generation, fallback_candidate.reply_text),
        )
        requires_review = bool(source_reasons)
        return ReplyRoutingOutcome(
            generation=combined_generation,
            requires_human_review=requires_review,
            metadata={
                "routing": "fallback_to_mini",
                "selected_model": fallback_generation.model_name,
                "escalation_reasons": escalation_reasons,
                "source_reasons": source_reasons,
            },
        )

    def _build_structured_system_prompt(self, system_prompt: str, *, max_reply_chars: int) -> str:
        return (
            f"{system_prompt}\n\n"
            "Return JSON only with these keys: "
            "reply_text, safe_to_send, confidence, escalate_to_mini, detected_tone, detected_intent, notes.\n"
            f"Keep reply_text plain text, concise, and under {max_reply_chars} characters.\n"
            "Do not include markdown, code fences, explanations, or extra keys."
        )

    @staticmethod
    def _build_structured_user_prompt(user_prompt: str) -> str:
        return f"{user_prompt}\nresponse_format: strict_json"

    def _parse_candidate(
        self,
        raw_content: str,
        *,
        max_reply_chars: int,
    ) -> tuple[StructuredReplyCandidate | None, list[str]]:
        payload = self._extract_json_object(raw_content)
        if payload is None:
            return None, ["reply_not_json"]

        required_fields = {"reply_text", "safe_to_send", "confidence", "escalate_to_mini"}
        missing_fields = sorted(required_fields - payload.keys())
        if missing_fields:
            return None, [f"missing_required_fields:{','.join(missing_fields)}"]

        reply_text = str(payload.get("reply_text", "")).strip()
        safe_to_send = payload.get("safe_to_send")
        confidence = payload.get("confidence")
        escalate_to_mini = payload.get("escalate_to_mini")

        errors: list[str] = []
        if not isinstance(safe_to_send, bool):
            errors.append("invalid_safe_to_send")
        if not isinstance(escalate_to_mini, bool):
            errors.append("invalid_escalate_to_mini")
        if not isinstance(confidence, int | float):
            errors.append("invalid_confidence")
        if not reply_text:
            errors.append("reply_empty")
        if len(reply_text) > max_reply_chars:
            errors.append("reply_too_long")
        if self._violates_business_rules(reply_text):
            errors.append("reply_violates_business_rules")
        if errors:
            return None, errors

        return (
            StructuredReplyCandidate(
                reply_text=reply_text,
                safe_to_send=bool(safe_to_send),
                confidence=float(confidence),
                escalate_to_mini=bool(escalate_to_mini),
                raw_payload=payload,
            ),
            [],
        )

    def _candidate_escalation_reasons(
        self,
        candidate: StructuredReplyCandidate | None,
        errors: list[str],
    ) -> list[str]:
        reasons = list(errors)
        if candidate is None:
            return reasons
        if candidate.escalate_to_mini:
            reasons.append("escalate_to_mini")
        if not candidate.safe_to_send:
            reasons.append("safe_to_send_false")
        if candidate.confidence < self.settings.openai_reply_confidence_threshold:
            reasons.append("confidence_below_threshold")
        return reasons

    @staticmethod
    def _source_escalation_reasons(*, source_text: str, instructions: str) -> list[str]:
        combined = "\n".join(part.strip() for part in (source_text, instructions) if part and part.strip())
        if not combined:
            return []

        lowered = combined.lower()
        reasons: list[str] = []
        if re.search(r"\b(angry|upset|frustrated|furious|terrible|worst|complain|complaint|refund|scam)\b", lowered):
            reasons.append("complaint_or_angry_tone")
        if re.search(r"\b(wholesale|bulk|reseller|resale|distributor|dealer|negotiat|best price|discount)\b", lowered):
            reasons.append("negotiation_or_bulk_order")
        if re.search(r"\b(ignore policy|override policy|bypass|guarantee|promise delivery|custom price)\b", lowered):
            reasons.append("policy_conflict")
        if len(combined) > 900 or combined.count("?") > 3 or combined.count("\n") > 12:
            reasons.append("long_or_ambiguous_context")
        return reasons

    @staticmethod
    def _violates_business_rules(reply_text: str) -> bool:
        lowered = reply_text.lower()
        if "```" in reply_text or lowered.startswith("{") or lowered.startswith("["):
            return True
        return any(
            phrase in lowered
            for phrase in (
                "as an ai",
                "i can't help with that",
                "i cannot help with that",
                "openai",
                "language model",
            )
        )

    @staticmethod
    def _extract_json_object(raw_content: str) -> dict[str, Any] | None:
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
        for candidate in (cleaned, ReplyRoutingService._first_braced_block(cleaned)):
            if not candidate:
                continue
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data
        return None

    @staticmethod
    def _first_braced_block(raw_content: str) -> str | None:
        start = raw_content.find("{")
        end = raw_content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return raw_content[start : end + 1]

    @staticmethod
    def _with_content(generation: LLMGenerationResult, content: str) -> LLMGenerationResult:
        return LLMGenerationResult(
            content=content.strip(),
            provider=generation.provider,
            model_name=generation.model_name,
            prompt_tokens=generation.prompt_tokens,
            completion_tokens=generation.completion_tokens,
        )

    @staticmethod
    def _combine_generations(
        primary_generation: LLMGenerationResult,
        fallback_generation: LLMGenerationResult,
    ) -> LLMGenerationResult:
        return LLMGenerationResult(
            content=fallback_generation.content,
            provider=fallback_generation.provider,
            model_name=fallback_generation.model_name,
            prompt_tokens=primary_generation.prompt_tokens + fallback_generation.prompt_tokens,
            completion_tokens=primary_generation.completion_tokens + fallback_generation.completion_tokens,
        )
