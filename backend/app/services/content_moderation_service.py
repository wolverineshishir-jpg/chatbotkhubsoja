from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class ModerationMatch:
    is_flagged: bool
    reason: str | None
    matched_terms: list[str]


class ContentModerationService:
    _BLOCKLIST = (
        "fuck",
        "fucking",
        "shit",
        "bitch",
        "bastard",
        "asshole",
        "motherfucker",
        "cunt",
        "slut",
        "dick",
        "nigga",
        "nigger",
        "whore",
        "chutiya",
        "madarchod",
        "bhenchod",
        "harami",
        "kutta",
        "bokachoda",
        "bal",
        "sala",
        "shalay",
        "khanki",
        "magi",
        "chod",
        "chodna",
        "fuck you",
        "bsdk",
    )

    def evaluate(self, text: str) -> ModerationMatch:
        normalized = self._normalize(text)
        matched_terms = [term for term in self._BLOCKLIST if self._contains_term(normalized, term)]
        if not matched_terms:
            return ModerationMatch(is_flagged=False, reason=None, matched_terms=[])

        unique_terms = sorted(set(matched_terms))
        return ModerationMatch(
            is_flagged=True,
            reason=f"Abusive or profane content detected: {', '.join(unique_terms[:5])}",
            matched_terms=unique_terms,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        lowered = text.lower()
        lowered = re.sub(r"[^a-z0-9\s]+", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        return lowered

    @staticmethod
    def _contains_term(normalized_text: str, term: str) -> bool:
        escaped = re.escape(term)
        pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
        return re.search(pattern, normalized_text) is not None
