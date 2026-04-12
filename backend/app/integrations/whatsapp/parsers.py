from __future__ import annotations

from app.integrations.whatsapp.schemas import ParsedWhatsAppMessageEvent, ParsedWhatsAppWebhook


class WhatsAppWebhookParser:
    def parse(self, payload: dict) -> ParsedWhatsAppWebhook:
        parsed = ParsedWhatsAppWebhook()
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                metadata = value.get("metadata", {})
                phone_number_id = str(metadata.get("phone_number_id") or "")
                contacts = value.get("contacts", [])
                contact = contacts[0] if contacts else {}
                sender_name = (contact.get("profile") or {}).get("name")
                for message in value.get("messages", []):
                    parsed_message = self._parse_message_event(
                        phone_number_id=phone_number_id,
                        sender_name=sender_name,
                        payload=message,
                    )
                    if parsed_message:
                        parsed.messages.append(parsed_message)
        return parsed

    @staticmethod
    def _parse_message_event(
        *,
        phone_number_id: str,
        sender_name: str | None,
        payload: dict,
    ) -> ParsedWhatsAppMessageEvent | None:
        message_id = payload.get("id")
        sender_id = payload.get("from")
        if not message_id or not sender_id:
            return None
        text = (
            (payload.get("text") or {}).get("body")
            or (payload.get("button") or {}).get("text")
            or (payload.get("interactive") or {}).get("button_reply", {}).get("title")
            or ""
        )
        return ParsedWhatsAppMessageEvent(
            phone_number_id=phone_number_id,
            sender_id=str(sender_id),
            sender_name=sender_name,
            message_id=str(message_id),
            text=text.strip(),
            created_time=str(payload.get("timestamp")) if payload.get("timestamp") else None,
            raw_payload=payload,
        )
