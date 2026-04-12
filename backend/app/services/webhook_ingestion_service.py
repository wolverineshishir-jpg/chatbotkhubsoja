import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import PlatformType, WebhookEventSource, WebhookEventStatus
from app.models.platform_connection import PlatformConnection
from app.models.webhook_event import WebhookEvent


class WebhookIngestionService:
    def __init__(self, db: Session):
        self.db = db

    def ingest_event(
        self,
        *,
        source: WebhookEventSource,
        platform_type: PlatformType,
        payload: dict,
        headers: dict[str, str],
    ) -> tuple[WebhookEvent, bool]:
        connection = self._resolve_connection(platform_type=platform_type, payload=payload, headers=headers)
        event_key = self._build_event_key(source=source, payload=payload, headers=headers, connection=connection)
        existing = self.db.scalar(select(WebhookEvent).where(WebhookEvent.event_key == event_key))
        if existing:
            return existing, False

        event = WebhookEvent(
            account_id=connection.account_id if connection else None,
            platform_connection_id=connection.id if connection else None,
            platform_type=platform_type,
            source=source,
            status=WebhookEventStatus.PENDING,
            event_type=self._event_type(platform_type=platform_type, payload=payload),
            event_key=event_key,
            delivery_id=headers.get("x-hub-signature-256")
            or headers.get("x-hub-signature")
            or headers.get("x-whatsapp-idempotency-key")
            or headers.get("x-request-id"),
            received_at=datetime.now(UTC),
            payload_json=payload,
            headers_json=headers,
            metadata_json={"connection_resolved": connection is not None},
        )
        self.db.add(event)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            existing = self.db.scalar(select(WebhookEvent).where(WebhookEvent.event_key == event_key))
            if existing:
                return existing, False
            raise

        self.db.refresh(event)
        return event, True

    def verify_webhook(self, *, platform_type: PlatformType, mode: str | None, token: str | None) -> bool:
        if not token:
            return False
        connection = self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.platform_type == platform_type,
                PlatformConnection.webhook_active.is_(True),
                PlatformConnection.webhook_verify_token == token,
            )
        )
        return mode == "subscribe" and connection is not None

    def _resolve_connection(
        self,
        *,
        platform_type: PlatformType,
        payload: dict,
        headers: dict[str, str],
    ) -> PlatformConnection | None:
        connection_id = headers.get("x-platform-connection-id")
        if connection_id and connection_id.isdigit():
            connection = self.db.get(PlatformConnection, int(connection_id))
            if connection and connection.platform_type == platform_type:
                return connection

        external_id = self._extract_external_id(platform_type=platform_type, payload=payload)
        if not external_id:
            return None
        return self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.platform_type == platform_type,
                PlatformConnection.external_id == external_id,
            )
        )

    @staticmethod
    def _extract_external_id(*, platform_type: PlatformType, payload: dict) -> str | None:
        if platform_type == PlatformType.FACEBOOK_PAGE:
            entries = payload.get("entry", [])
            if entries:
                return str(entries[0].get("id")) if entries[0].get("id") else None
            return None

        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                metadata = change.get("value", {}).get("metadata", {})
                phone_number_id = metadata.get("phone_number_id")
                if phone_number_id:
                    return str(phone_number_id)
        return None

    @staticmethod
    def _event_type(*, platform_type: PlatformType, payload: dict) -> str:
        if platform_type == PlatformType.FACEBOOK_PAGE:
            if any(entry.get("messaging") for entry in payload.get("entry", [])):
                return "inbound_message"
            if any(entry.get("changes") for entry in payload.get("entry", [])):
                return "inbound_comment"
            return "facebook_event"
        entries = payload.get("entry", [])
        if any((change.get("value") or {}).get("messages") for entry in entries for change in entry.get("changes", [])):
            return "inbound_message"
        return "whatsapp_event"

    @staticmethod
    def _build_event_key(
        *,
        source: WebhookEventSource,
        payload: dict,
        headers: dict[str, str],
        connection: PlatformConnection | None,
    ) -> str:
        pieces = [
            source.value,
            str(connection.id if connection else "unknown"),
            headers.get("x-hub-signature-256") or "",
            headers.get("x-whatsapp-idempotency-key") or "",
            headers.get("x-request-id") or "",
            repr(payload),
        ]
        return hashlib.sha256("|".join(pieces).encode("utf-8")).hexdigest()
