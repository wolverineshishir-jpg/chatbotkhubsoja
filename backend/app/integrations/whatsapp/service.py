from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.whatsapp.client import WhatsAppCloudAPIClient, WhatsAppCloudAPIError
from app.models.account import Account
from app.models.enums import ConnectionStatus, PlatformType
from app.models.platform_connection import PlatformConnection
from app.utils.crypto import token_cipher


class WhatsAppIntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self.client = WhatsAppCloudAPIClient()

    def connect_phone_number_manually(
        self,
        *,
        account: Account,
        phone_number_id: str,
        access_token: str,
        connection_name: str | None,
        business_account_id: str | None = None,
        display_phone_number: str | None = None,
        webhook_verify_token: str | None = None,
        webhook_secret: str | None = None,
    ) -> PlatformConnection:
        profile = self.client.get_phone_number_profile(phone_number_id=phone_number_id, access_token=access_token)
        return self._upsert_connection(
            account=account,
            phone_number_id=profile.phone_number_id,
            display_phone_number=display_phone_number or profile.display_phone_number,
            verified_name=profile.verified_name,
            quality_rating=profile.quality_rating,
            access_token=access_token,
            business_account_id=business_account_id,
            connection_name=connection_name,
            webhook_verify_token=webhook_verify_token,
            webhook_secret=webhook_secret,
            connected_via="manual",
        )

    def sync_connection(self, connection: PlatformConnection) -> PlatformConnection:
        profile = self.client.get_phone_number_profile(
            phone_number_id=self.phone_number_id(connection),
            access_token=self.get_access_token(connection),
        )
        whatsapp_meta = self.whatsapp_meta(connection)
        whatsapp_meta.update(
            {
                "display_phone_number": profile.display_phone_number,
                "verified_name": profile.verified_name,
                "quality_rating": profile.quality_rating,
                "last_synced_at": self.utcnow().isoformat(),
                "sync_state": "synced",
                "token_status": "valid",
            }
        )
        connection.external_id = profile.phone_number_id
        connection.external_name = profile.display_phone_number or connection.external_name
        connection.metadata_json = {**(connection.metadata_json or {}), "whatsapp": whatsapp_meta}
        connection.status = ConnectionStatus.CONNECTED
        connection.last_error = None
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def verify_signature(self, *, raw_body: bytes, signature_header: str | None) -> bool:
        return self.client.verify_webhook_signature(raw_body=raw_body, signature_header=signature_header)

    def get_access_token(self, connection: PlatformConnection) -> str:
        token = token_cipher.decrypt(connection.encrypted_access_token)
        if not token:
            raise WhatsAppCloudAPIError("No WhatsApp access token is stored for this connection.")
        return token

    def handle_api_error(self, *, connection: PlatformConnection, exc: WhatsAppCloudAPIError) -> None:
        whatsapp_meta = self.whatsapp_meta(connection)
        whatsapp_meta["last_api_error"] = {
            "message": str(exc),
            "code": exc.code,
            "subcode": exc.subcode,
            "recorded_at": self.utcnow().isoformat(),
        }
        whatsapp_meta["token_status"] = "action_required" if (exc.is_token_error or exc.is_permission_error) else "error"
        connection.status = (
            ConnectionStatus.ACTION_REQUIRED if (exc.is_token_error or exc.is_permission_error) else ConnectionStatus.ERROR
        )
        connection.last_error = str(exc)[:500]
        connection.metadata_json = {**(connection.metadata_json or {}), "whatsapp": whatsapp_meta}
        self.db.commit()

    def integration_summary(self, connection: PlatformConnection) -> dict[str, Any]:
        meta = self.whatsapp_meta(connection)
        return {
            "provider": "whatsapp",
            "connected_via": meta.get("connected_via"),
            "sync_state": meta.get("sync_state", "pending"),
            "token_status": meta.get("token_status", "unknown"),
            "last_synced_at": meta.get("last_synced_at"),
            "webhook_subscription_state": "active" if connection.webhook_active else "inactive",
            "required_permissions": ["whatsapp_business_messaging"],
            "tasks": ["inbound_message", "outbound_message"],
        }

    @staticmethod
    def whatsapp_meta(connection: PlatformConnection) -> dict[str, Any]:
        return dict((connection.metadata_json or {}).get("whatsapp") or {})

    @staticmethod
    def phone_number_id(connection: PlatformConnection) -> str:
        number_id = ((connection.metadata_json or {}).get("whatsapp") or {}).get("phone_number_id") or connection.external_id
        if not number_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="WhatsApp phone_number_id is missing for this connection.",
            )
        return str(number_id)

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(UTC)

    def _upsert_connection(
        self,
        *,
        account: Account,
        phone_number_id: str,
        display_phone_number: str | None,
        verified_name: str | None,
        quality_rating: str | None,
        access_token: str,
        business_account_id: str | None,
        connection_name: str | None,
        webhook_verify_token: str | None,
        webhook_secret: str | None,
        connected_via: str,
    ) -> PlatformConnection:
        existing = self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.account_id == account.id,
                PlatformConnection.platform_type == PlatformType.WHATSAPP,
                PlatformConnection.external_id == phone_number_id,
            )
        )
        connection = existing or PlatformConnection(account_id=account.id, platform_type=PlatformType.WHATSAPP)
        connection.name = connection_name or display_phone_number or verified_name or f"WhatsApp {phone_number_id}"
        connection.external_id = phone_number_id
        connection.external_name = display_phone_number or verified_name
        connection.encrypted_access_token = token_cipher.encrypt(access_token)
        connection.token_hint = self._token_hint(access_token)
        connection.webhook_verify_token = (
            webhook_verify_token or connection.webhook_verify_token or f"wa-{account.id}-{phone_number_id}"
        )
        if webhook_secret:
            connection.webhook_secret = webhook_secret
        connection.metadata_json = {
            **(connection.metadata_json or {}),
            "whatsapp": {
                **self.whatsapp_meta(connection),
                "phone_number_id": phone_number_id,
                "business_account_id": business_account_id,
                "display_phone_number": display_phone_number,
                "verified_name": verified_name,
                "quality_rating": quality_rating,
                "connected_via": connected_via,
                "token_status": "valid",
                "sync_state": "connected",
                "last_synced_at": self.utcnow().isoformat(),
            },
        }
        connection.status = ConnectionStatus.CONNECTED
        connection.last_error = None
        if existing is None:
            self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        return connection

    @staticmethod
    def _token_hint(token: str | None) -> str | None:
        if not token:
            return None
        tail = token[-4:] if len(token) >= 4 else token
        return f"...{tail}"
