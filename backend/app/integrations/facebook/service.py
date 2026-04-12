from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.facebook.client import FacebookGraphAPIClient, FacebookGraphAPIError
from app.integrations.facebook.oauth_sessions import FacebookOAuthSessionStore
from app.integrations.facebook.schemas import FacebookPageCandidate
from app.models.account import Account
from app.models.enums import ConnectionStatus, PlatformType
from app.models.platform_connection import PlatformConnection
from app.models.user import User
from app.utils.crypto import token_cipher


class FacebookIntegrationService:
    OAUTH_SCOPES = [
        "pages_show_list",
        "pages_manage_metadata",
        "pages_messaging",
        "pages_read_engagement",
        "pages_manage_posts",
        "pages_manage_engagement",
    ]

    def __init__(self, db: Session):
        self.db = db
        self.client = FacebookGraphAPIClient()
        self.settings = get_settings()
        self.oauth_sessions = FacebookOAuthSessionStore()

    def start_oauth(self, *, account: Account, actor: User) -> dict[str, Any]:
        if not self.settings.facebook_app_id:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Facebook OAuth is not configured on the server.",
            )
        state = self.oauth_sessions.create(
            {
                "account_id": account.id,
                "actor_user_id": actor.id,
                "redirect_uri": self.settings.facebook_oauth_redirect_uri,
            }
        )
        return {
            "state": state,
            "auth_url": self.client.build_oauth_url(
                state=state,
                redirect_uri=self.settings.facebook_oauth_redirect_uri,
                scopes=self.OAUTH_SCOPES,
            ),
            "redirect_uri": self.settings.facebook_oauth_redirect_uri,
            "scopes": self.OAUTH_SCOPES,
        }

    def complete_oauth(self, *, account: Account, actor: User, state: str, code: str) -> dict[str, Any]:
        session = self._get_valid_session(state=state, account=account, actor=actor)
        user_token = self.client.exchange_code_for_user_token(
            code=code,
            redirect_uri=session["redirect_uri"],
        )["access_token"]
        token_payload = self.client.exchange_for_long_lived_user_token(access_token=user_token)
        long_lived_user_token = token_payload["access_token"]
        pages = self.client.list_managed_pages(access_token=long_lived_user_token)
        self.oauth_sessions.save(
            state,
            {
                **session,
                "long_lived_user_token": long_lived_user_token,
                "pages": [self._serialize_page(page) for page in pages],
            },
        )
        return {"state": state, "pages": [self._page_response(page) for page in pages]}

    def connect_page_from_oauth(
        self,
        *,
        account: Account,
        actor: User,
        state: str,
        page_id: str,
        connection_name: str | None,
        webhook_verify_token: str | None = None,
        webhook_secret: str | None = None,
    ) -> PlatformConnection:
        session = self._get_valid_session(state=state, account=account, actor=actor)
        pages = [self._deserialize_page(item) for item in session.get("pages", [])]
        page = next((item for item in pages if item.page_id == page_id), None)
        if page is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected Facebook Page was not found in the OAuth session.")
        connection = self._upsert_connection(
            account=account,
            page=page,
            connection_name=connection_name,
            user_access_token=session.get("long_lived_user_token"),
            webhook_verify_token=webhook_verify_token,
            webhook_secret=webhook_secret,
            connected_via="oauth",
        )
        self.oauth_sessions.delete(state)
        return connection

    def connect_page_from_manual_token(
        self,
        *,
        account: Account,
        page_id: str,
        page_access_token: str,
        connection_name: str | None,
        user_access_token: str | None = None,
        webhook_verify_token: str | None = None,
        webhook_secret: str | None = None,
    ) -> PlatformConnection:
        profile = self.client.get_page_profile(page_id=page_id, access_token=page_access_token)
        page = FacebookPageCandidate(
            page_id=profile.page_id,
            page_name=profile.page_name,
            page_access_token=page_access_token,
            category=profile.category,
            picture_url=profile.picture_url,
        )
        return self._upsert_connection(
            account=account,
            page=page,
            connection_name=connection_name,
            user_access_token=user_access_token,
            webhook_verify_token=webhook_verify_token,
            webhook_secret=webhook_secret,
            connected_via="manual",
        )

    def sync_connection(self, connection: PlatformConnection) -> PlatformConnection:
        page_token = self.get_page_access_token(connection)
        profile = self.client.get_page_profile(page_id=self.page_id(connection), access_token=page_token)
        subscriptions = self.client.get_page_subscriptions(page_id=self.page_id(connection), access_token=page_token)
        is_subscribed = self._has_active_subscription(subscriptions)
        facebook_meta = self.facebook_meta(connection)
        facebook_meta.update(
            {
                "page_name": profile.page_name,
                "page_category": profile.category,
                "page_picture_url": profile.picture_url,
                "followers_count": profile.followers_count,
                "last_synced_at": self.utcnow().isoformat(),
                "sync_state": "synced",
                "token_status": "valid",
                "webhook_subscription_state": "subscribed" if is_subscribed else "inactive",
            }
        )
        connection.external_id = profile.page_id
        connection.external_name = profile.page_name
        connection.metadata_json = {**(connection.metadata_json or {}), "facebook": facebook_meta}
        connection.webhook_active = is_subscribed
        connection.last_error = None
        connection.status = ConnectionStatus.CONNECTED
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def subscribe_webhooks(self, connection: PlatformConnection) -> PlatformConnection:
        page_token = self.get_page_access_token(connection)
        self.client.subscribe_page_to_app(page_id=self.page_id(connection), access_token=page_token)
        subscriptions = self.client.get_page_subscriptions(page_id=self.page_id(connection), access_token=page_token)
        is_subscribed = self._has_active_subscription(subscriptions)
        facebook_meta = self.facebook_meta(connection)
        facebook_meta["webhook_subscription_state"] = "subscribed" if is_subscribed else "inactive"
        facebook_meta["last_synced_at"] = self.utcnow().isoformat()
        connection.metadata_json = {**(connection.metadata_json or {}), "facebook": facebook_meta}
        connection.webhook_active = is_subscribed
        connection.last_error = None
        if not is_subscribed:
            raise FacebookGraphAPIError(
                "Facebook did not confirm the Page webhook subscription. Check Page permissions, then sync and try again."
            )
        connection.status = ConnectionStatus.CONNECTED
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def verify_signature(self, *, raw_body: bytes, signature_header: str | None) -> bool:
        return self.client.verify_webhook_signature(raw_body=raw_body, signature_header=signature_header)

    def get_page_access_token(self, connection: PlatformConnection) -> str:
        token = token_cipher.decrypt(connection.encrypted_access_token)
        if not token:
            raise FacebookGraphAPIError("No Facebook Page access token is stored for this connection.")
        return token

    def get_user_access_token(self, connection: PlatformConnection) -> str | None:
        return token_cipher.decrypt(connection.encrypted_refresh_token)

    def handle_api_error(self, *, connection: PlatformConnection, exc: FacebookGraphAPIError) -> None:
        facebook_meta = self.facebook_meta(connection)
        facebook_meta["last_api_error"] = {
            "message": str(exc),
            "code": exc.code,
            "subcode": exc.subcode,
            "recorded_at": self.utcnow().isoformat(),
        }
        facebook_meta["token_status"] = "action_required" if (exc.is_token_error or exc.is_permission_error) else "error"
        connection.status = (
            ConnectionStatus.ACTION_REQUIRED if (exc.is_token_error or exc.is_permission_error) else ConnectionStatus.ERROR
        )
        connection.last_error = str(exc)[:500]
        connection.metadata_json = {**(connection.metadata_json or {}), "facebook": facebook_meta}
        self.db.commit()

    def integration_summary(self, connection: PlatformConnection) -> dict[str, Any]:
        meta = self.facebook_meta(connection)
        return {
            "provider": "facebook",
            "connected_via": meta.get("connected_via"),
            "sync_state": meta.get("sync_state", "pending"),
            "token_status": meta.get("token_status", "unknown"),
            "last_synced_at": meta.get("last_synced_at"),
            "webhook_subscription_state": meta.get("webhook_subscription_state"),
            "page_picture_url": meta.get("page_picture_url"),
            "followers_count": meta.get("followers_count"),
            "required_permissions": self.OAUTH_SCOPES,
            "tasks": meta.get("tasks", []),
        }

    @staticmethod
    def _has_active_subscription(subscriptions: dict[str, Any]) -> bool:
        return bool(subscriptions.get("data"))

    @staticmethod
    def facebook_meta(connection: PlatformConnection) -> dict[str, Any]:
        return dict((connection.metadata_json or {}).get("facebook") or {})

    @staticmethod
    def page_id(connection: PlatformConnection) -> str:
        page_id = ((connection.metadata_json or {}).get("facebook") or {}).get("page_id") or connection.external_id
        if not page_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Facebook Page ID is missing for this connection.")
        return str(page_id)

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(UTC)

    def _upsert_connection(
        self,
        *,
        account: Account,
        page: FacebookPageCandidate,
        connection_name: str | None,
        user_access_token: str | None,
        webhook_verify_token: str | None,
        webhook_secret: str | None,
        connected_via: str,
    ) -> PlatformConnection:
        existing = self.db.scalar(
            select(PlatformConnection).where(
                PlatformConnection.account_id == account.id,
                PlatformConnection.platform_type == PlatformType.FACEBOOK_PAGE,
                PlatformConnection.external_id == page.page_id,
            )
        )
        connection = existing or PlatformConnection(account_id=account.id, platform_type=PlatformType.FACEBOOK_PAGE)
        connection.name = connection_name or page.page_name
        connection.external_id = page.page_id
        connection.external_name = page.page_name
        connection.encrypted_access_token = token_cipher.encrypt(page.page_access_token)
        if user_access_token:
            connection.encrypted_refresh_token = token_cipher.encrypt(user_access_token)
        connection.token_hint = self._token_hint(page.page_access_token)
        connection.webhook_verify_token = webhook_verify_token or connection.webhook_verify_token or f"fb-{account.id}-{page.page_id}"
        if webhook_secret:
            connection.webhook_secret = webhook_secret
        connection.metadata_json = {
            **(connection.metadata_json or {}),
            "facebook": {
                **self.facebook_meta(connection),
                "page_id": page.page_id,
                "page_name": page.page_name,
                "page_category": page.category,
                "page_picture_url": page.picture_url,
                "tasks": page.tasks,
                "connected_via": connected_via,
                "token_status": "valid",
                "sync_state": "connected",
                "last_synced_at": self.utcnow().isoformat(),
                "webhook_subscription_state": "pending",
            },
        }
        connection.status = ConnectionStatus.CONNECTED
        connection.last_error = None
        if existing is None:
            self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def _get_valid_session(self, *, state: str, account: Account, actor: User) -> dict[str, Any]:
        session = self.oauth_sessions.get(state)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facebook OAuth session not found or expired.")
        if session.get("account_id") != account.id or session.get("actor_user_id") != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facebook OAuth session does not belong to the active account.")
        return session

    @staticmethod
    def _serialize_page(page: FacebookPageCandidate) -> dict[str, Any]:
        return {
            "page_id": page.page_id,
            "page_name": page.page_name,
            "page_access_token": page.page_access_token,
            "category": page.category,
            "tasks": page.tasks,
            "picture_url": page.picture_url,
        }

    @staticmethod
    def _deserialize_page(payload: dict[str, Any]) -> FacebookPageCandidate:
        return FacebookPageCandidate(
            page_id=payload["page_id"],
            page_name=payload["page_name"],
            page_access_token=payload["page_access_token"],
            category=payload.get("category"),
            tasks=payload.get("tasks", []),
            picture_url=payload.get("picture_url"),
        )

    @staticmethod
    def _page_response(page: FacebookPageCandidate) -> dict[str, Any]:
        return {
            "page_id": page.page_id,
            "page_name": page.page_name,
            "category": page.category,
            "tasks": page.tasks,
            "picture_url": page.picture_url,
        }

    @staticmethod
    def _token_hint(token: str | None) -> str | None:
        if not token:
            return None
        tail = token[-4:] if len(token) >= 4 else token
        return f"...{tail}"
