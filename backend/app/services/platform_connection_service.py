from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from app.models.account import Account
from app.models.enums import ConnectionStatus, PlatformType
from app.models.platform_connection import PlatformConnection
from app.integrations.facebook import FacebookGraphAPIError, FacebookIntegrationService
from app.integrations.whatsapp import WhatsAppCloudAPIError, WhatsAppIntegrationService
from app.schemas.platform_connection import (
    FacebookManualConnectRequest,
    WhatsAppManualConnectRequest,
    PlatformConnectionCreateRequest,
    PlatformConnectionResponse,
    PlatformConnectionStatusUpdateRequest,
    PlatformConnectionUpdateRequest,
    IntegrationSummaryResponse,
    WebhookConfigResponse,
)
from app.utils.crypto import token_cipher


class PlatformConnectionService:
    def __init__(self, db: Session):
        self.db = db
        self.facebook = FacebookIntegrationService(db)
        self.whatsapp = WhatsAppIntegrationService(db)

    def list_connections(self, account: Account) -> list[PlatformConnectionResponse]:
        connections = self.db.scalars(
            select(PlatformConnection)
            .where(PlatformConnection.account_id == account.id)
            .order_by(PlatformConnection.created_at.desc())
        ).all()
        return [self._to_response(connection) for connection in connections]

    def get_connection(self, account: Account, connection_id: int) -> PlatformConnectionResponse:
        connection = self._get_connection_for_account(account.id, connection_id)
        return self._to_response(connection)

    def create_connection(
        self, account: Account, payload: PlatformConnectionCreateRequest
    ) -> PlatformConnectionResponse:
        connection = PlatformConnection(
            account_id=account.id,
            platform_type=payload.platform_type,
            name=payload.name,
            external_id=payload.external_id,
            external_name=payload.external_name,
            encrypted_access_token=token_cipher.encrypt(payload.access_token),
            encrypted_refresh_token=token_cipher.encrypt(payload.refresh_token),
            token_hint=self._token_hint(payload.access_token),
            metadata_json=payload.metadata_json,
            settings_json=payload.settings_json,
        )

        self._apply_webhook(connection, payload.webhook)
        self._sync_status(connection)

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        return self._to_response(connection)

    def update_connection(
        self,
        account: Account,
        connection_id: int,
        payload: PlatformConnectionUpdateRequest,
    ) -> PlatformConnectionResponse:
        connection = self._get_connection_for_account(account.id, connection_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field in ("name", "external_id", "external_name", "last_error"):
            if field in update_data:
                setattr(connection, field, update_data[field])

        if "metadata_json" in update_data and payload.metadata_json is not None:
            connection.metadata_json = payload.metadata_json
        if "settings_json" in update_data and payload.settings_json is not None:
            connection.settings_json = payload.settings_json
        if "access_token" in update_data:
            connection.encrypted_access_token = token_cipher.encrypt(payload.access_token)
            connection.token_hint = self._token_hint(payload.access_token)
        if "refresh_token" in update_data:
            connection.encrypted_refresh_token = token_cipher.encrypt(payload.refresh_token)
        if "webhook" in update_data:
            self._apply_webhook(connection, payload.webhook)

        self._sync_status(connection)
        self.db.commit()
        self.db.refresh(connection)
        return self._to_response(connection)

    def update_status(
        self,
        account: Account,
        connection_id: int,
        payload: PlatformConnectionStatusUpdateRequest,
    ) -> PlatformConnectionResponse:
        connection = self._get_connection_for_account(account.id, connection_id)
        connection.status = payload.status
        connection.last_error = payload.last_error
        self.db.commit()
        self.db.refresh(connection)
        return self._to_response(connection)

    def disconnect_connection(self, account: Account, connection_id: int) -> PlatformConnectionResponse:
        connection = self._get_connection_for_account(account.id, connection_id)
        connection.status = ConnectionStatus.DISCONNECTED
        connection.encrypted_access_token = None
        connection.encrypted_refresh_token = None
        connection.token_hint = None
        connection.last_error = None
        self.db.commit()
        self.db.refresh(connection)
        return self._to_response(connection)

    def delete_connection(self, account: Account, connection_id: int) -> None:
        connection = self._get_connection_for_account(account.id, connection_id)
        self.db.delete(connection)
        self.db.commit()

    def connect_facebook_page_manually(
        self,
        *,
        account: Account,
        payload: FacebookManualConnectRequest,
    ) -> PlatformConnectionResponse:
        connection = self.facebook.connect_page_from_manual_token(
            account=account,
            page_id=payload.page_id,
            page_access_token=payload.page_access_token,
            connection_name=payload.connection_name,
            user_access_token=payload.user_access_token,
            webhook_verify_token=payload.webhook_verify_token,
            webhook_secret=payload.webhook_secret,
        )
        return self._to_response(connection)

    def connect_whatsapp_manually(
        self,
        *,
        account: Account,
        payload: WhatsAppManualConnectRequest,
    ) -> PlatformConnectionResponse:
        connection = self.whatsapp.connect_phone_number_manually(
            account=account,
            phone_number_id=payload.phone_number_id,
            access_token=payload.access_token,
            connection_name=payload.connection_name,
            business_account_id=payload.business_account_id,
            display_phone_number=payload.display_phone_number,
            webhook_verify_token=payload.webhook_verify_token,
            webhook_secret=payload.webhook_secret,
        )
        return self._to_response(connection)

    def sync_facebook_connection(self, *, account: Account, connection_id: int) -> PlatformConnectionResponse:
        connection = self._get_connection_for_account(account.id, connection_id)
        if connection.platform_type != PlatformType.FACEBOOK_PAGE:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only Facebook Page connections support this sync endpoint.")
        try:
            connection = self.facebook.sync_connection(connection)
        except FacebookGraphAPIError as exc:
            self.facebook.handle_api_error(connection=connection, exc=exc)
            self.db.refresh(connection)
        return self._to_response(connection)

    def subscribe_facebook_webhooks(self, *, account: Account, connection_id: int) -> PlatformConnectionResponse:
        connection = self._get_connection_for_account(account.id, connection_id)
        if connection.platform_type != PlatformType.FACEBOOK_PAGE:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only Facebook Page connections support webhook subscription.")
        try:
            connection = self.facebook.subscribe_webhooks(connection)
        except FacebookGraphAPIError as exc:
            self.facebook.handle_api_error(connection=connection, exc=exc)
            self.db.refresh(connection)
        return self._to_response(connection)

    def sync_whatsapp_connection(self, *, account: Account, connection_id: int) -> PlatformConnectionResponse:
        connection = self._get_connection_for_account(account.id, connection_id)
        if connection.platform_type != PlatformType.WHATSAPP:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only WhatsApp connections support this sync endpoint.",
            )
        try:
            connection = self.whatsapp.sync_connection(connection)
        except WhatsAppCloudAPIError as exc:
            self.whatsapp.handle_api_error(connection=connection, exc=exc)
            self.db.refresh(connection)
        return self._to_response(connection)

    def _get_connection_for_account(self, account_id: int, connection_id: int) -> PlatformConnection:
        connection = self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.id == connection_id,
                PlatformConnection.account_id == account_id,
            )
        )
        if not connection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform connection not found.")
        return connection

    def _sync_status(self, connection: PlatformConnection) -> None:
        if connection.status == ConnectionStatus.DISCONNECTED:
            return
        if connection.last_error:
            connection.status = ConnectionStatus.ERROR
        elif connection.encrypted_access_token:
            connection.status = ConnectionStatus.CONNECTED
        else:
            connection.status = ConnectionStatus.PENDING

    @staticmethod
    def _apply_webhook(connection: PlatformConnection, payload) -> None:
        if payload is None:
            return
        connection.webhook_url = str(payload.webhook_url) if payload.webhook_url else None
        connection.webhook_secret = payload.webhook_secret
        connection.webhook_verify_token = payload.webhook_verify_token
        connection.webhook_active = payload.webhook_active

    @staticmethod
    def _token_hint(token: str | None) -> str | None:
        if not token:
            return None
        tail = token[-4:] if len(token) >= 4 else token
        return f"...{tail}"

    def _to_response(self, connection: PlatformConnection) -> PlatformConnectionResponse:
        integration_summary = None
        if connection.platform_type == PlatformType.FACEBOOK_PAGE:
            integration_summary = IntegrationSummaryResponse.model_validate(self.facebook.integration_summary(connection))
        elif connection.platform_type == PlatformType.WHATSAPP:
            integration_summary = IntegrationSummaryResponse.model_validate(self.whatsapp.integration_summary(connection))
        return PlatformConnectionResponse(
            id=connection.id,
            account_id=connection.account_id,
            platform_type=connection.platform_type,
            name=connection.name,
            external_id=connection.external_id,
            external_name=connection.external_name,
            status=connection.status,
            token_hint=connection.token_hint,
            webhook=WebhookConfigResponse(
                webhook_url=connection.webhook_url,
                webhook_active=connection.webhook_active,
                has_secret=bool(connection.webhook_secret),
                has_verify_token=bool(connection.webhook_verify_token),
            ),
            metadata_json=connection.metadata_json or {},
            settings_json=connection.settings_json or {},
            last_error=connection.last_error,
            integration_summary=integration_summary,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
