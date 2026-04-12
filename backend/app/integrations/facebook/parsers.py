from __future__ import annotations

from app.integrations.facebook.schemas import ParsedCommentEvent, ParsedFacebookWebhook, ParsedMessengerEvent


class FacebookWebhookParser:
    def parse(self, payload: dict) -> ParsedFacebookWebhook:
        parsed = ParsedFacebookWebhook()
        for entry in payload.get("entry", []):
            page_id = str(entry.get("id") or "")
            for messaging in entry.get("messaging", []):
                event = self._parse_messaging_event(page_id=page_id, payload=messaging)
                if event:
                    parsed.messages.append(event)
            for change in entry.get("changes", []):
                event = self._parse_change_event(page_id=page_id, payload=change)
                if event:
                    parsed.comments.append(event)
        return parsed

    @staticmethod
    def _parse_messaging_event(*, page_id: str, payload: dict) -> ParsedMessengerEvent | None:
        message = payload.get("message") or {}
        if not message or message.get("is_echo"):
            return None
        message_id = message.get("mid")
        text = message.get("text") or payload.get("postback", {}).get("title") or ""
        if not message_id or not text:
            return None
        return ParsedMessengerEvent(
            page_id=page_id,
            sender_id=str((payload.get("sender") or {}).get("id") or ""),
            recipient_id=str((payload.get("recipient") or {}).get("id") or "") or None,
            message_id=str(message_id),
            text=text,
            created_time=str(payload.get("timestamp")) if payload.get("timestamp") else None,
            raw_payload=payload,
        )

    @staticmethod
    def _parse_change_event(*, page_id: str, payload: dict) -> ParsedCommentEvent | None:
        field = payload.get("field")
        value = payload.get("value") or {}
        if field not in {"feed", "comments"} or value.get("item") != "comment":
            return None
        comment_id = value.get("comment_id") or value.get("post_id")
        if not comment_id:
            return None
        return ParsedCommentEvent(
            page_id=page_id,
            comment_id=str(comment_id),
            post_id=str(value.get("post_id")) if value.get("post_id") else None,
            parent_id=str(value.get("parent_id")) if value.get("parent_id") else None,
            commenter_id=str((value.get("from") or {}).get("id")) if (value.get("from") or {}).get("id") else None,
            commenter_name=(value.get("from") or {}).get("name"),
            message=value.get("message") or value.get("verb") or "",
            created_time=str(value.get("created_time")) if value.get("created_time") else None,
            raw_payload=payload,
        )
