from __future__ import annotations

from pydantic import BaseModel, Field


class WhatsAppPhoneNumberProfile(BaseModel):
    phone_number_id: str
    display_phone_number: str | None = None
    verified_name: str | None = None
    quality_rating: str | None = None


class ParsedWhatsAppMessageEvent(BaseModel):
    phone_number_id: str
    sender_id: str
    sender_name: str | None = None
    message_id: str
    text: str
    created_time: str | None = None
    raw_payload: dict = Field(default_factory=dict)


class ParsedWhatsAppWebhook(BaseModel):
    messages: list[ParsedWhatsAppMessageEvent] = Field(default_factory=list)
