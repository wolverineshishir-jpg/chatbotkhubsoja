from __future__ import annotations

import hashlib
import hmac
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.integrations.facebook.schemas import FacebookPageCandidate, FacebookPageProfile


class FacebookGraphAPIError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        subcode: int | None = None,
        status_code: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.subcode = subcode
        self.status_code = status_code
        self.payload = payload or {}

    @property
    def is_token_error(self) -> bool:
        return self.code in {102, 190} or self.subcode in {460, 463, 467}

    @property
    def is_permission_error(self) -> bool:
        return self.code in {10, 200}


class FacebookGraphAPIClient:
    PAGE_SUBSCRIBED_FIELDS = [
        "messages",
        "messaging_postbacks",
        "feed",
    ]

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = f"{self.settings.facebook_graph_api_base_url}/{self.settings.facebook_graph_api_version}"
        self.oauth_base_url = f"{self.settings.facebook_graph_api_base_url}/{self.settings.facebook_graph_api_version}/oauth"

    def build_oauth_url(self, *, state: str, redirect_uri: str, scopes: list[str]) -> str:
        params = urlencode(
            {
                "client_id": self.settings.facebook_app_id,
                "redirect_uri": redirect_uri,
                "scope": ",".join(scopes),
                "state": state,
                "response_type": "code",
            }
        )
        return f"{self.settings.facebook_oauth_dialog_url}?{params}"

    def exchange_code_for_user_token(self, *, code: str, redirect_uri: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"{self.oauth_base_url}/access_token",
            absolute_url=True,
            params={
                "client_id": self.settings.facebook_app_id,
                "client_secret": self.settings.facebook_app_secret.get_secret_value(),
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )

    def exchange_for_long_lived_user_token(self, *, access_token: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"{self.oauth_base_url}/access_token",
            absolute_url=True,
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.settings.facebook_app_id,
                "client_secret": self.settings.facebook_app_secret.get_secret_value(),
                "fb_exchange_token": access_token,
            },
        )

    def list_managed_pages(self, *, access_token: str) -> list[FacebookPageCandidate]:
        data = self._request(
            "GET",
            "/me/accounts",
            access_token=access_token,
            params={"fields": "id,name,access_token,category,tasks,picture{url}"},
        )
        return [
            FacebookPageCandidate(
                page_id=str(item["id"]),
                page_name=item["name"],
                page_access_token=item["access_token"],
                category=item.get("category"),
                tasks=item.get("tasks", []),
                picture_url=((item.get("picture") or {}).get("data") or {}).get("url"),
            )
            for item in data.get("data", [])
        ]

    def get_page_profile(self, *, page_id: str, access_token: str) -> FacebookPageProfile:
        data = self._request(
            "GET",
            f"/{page_id}",
            access_token=access_token,
            params={"fields": "id,name,category,followers_count,picture{url}"},
        )
        return FacebookPageProfile(
            page_id=str(data["id"]),
            page_name=data["name"],
            category=data.get("category"),
            followers_count=data.get("followers_count"),
            picture_url=((data.get("picture") or {}).get("data") or {}).get("url"),
        )

    def subscribe_page_to_app(self, *, page_id: str, access_token: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/{page_id}/subscribed_apps",
            access_token=access_token,
            params={"subscribed_fields": ",".join(self.PAGE_SUBSCRIBED_FIELDS)},
        )

    def get_page_subscriptions(self, *, page_id: str, access_token: str) -> dict[str, Any]:
        return self._request("GET", f"/{page_id}/subscribed_apps", access_token=access_token)

    def send_message(self, *, page_access_token: str, recipient_id: str, text: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/me/messages",
            access_token=page_access_token,
            json={
                "recipient": {"id": recipient_id},
                "messaging_type": "RESPONSE",
                "message": {"text": text},
            },
        )

    def reply_to_comment(self, *, page_access_token: str, comment_id: str, text: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/{comment_id}/comments",
            access_token=page_access_token,
            json={"message": text},
        )

    def publish_post(
        self,
        *,
        page_access_token: str,
        page_id: str,
        message: str,
        link: str | None = None,
        published: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": message, "published": published}
        if link:
            payload["link"] = link
        return self._request(
            "POST",
            f"/{page_id}/feed",
            access_token=page_access_token,
            json=payload,
        )

    def verify_webhook_signature(self, *, raw_body: bytes, signature_header: str | None) -> bool:
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        expected = hmac.new(
            self.settings.facebook_app_secret.get_secret_value().encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature_header.split("=", 1)[1], expected)

    def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        absolute_url: bool = False,
    ) -> dict[str, Any]:
        url = path if absolute_url else f"{self.base_url}{path}"
        request_params = dict(params or {})
        if access_token:
            request_params["access_token"] = access_token

        with httpx.Client(timeout=self.settings.facebook_http_timeout_seconds) as client:
            response = client.request(method, url, params=request_params or None, json=json)

        if response.status_code >= 400:
            self._raise_error(response)

        data = response.json()
        if "error" in data:
            error = data["error"]
            raise FacebookGraphAPIError(
                error.get("message", "Facebook API request failed."),
                code=error.get("code"),
                subcode=error.get("error_subcode"),
                status_code=response.status_code,
                payload=data,
            )
        return data

    @staticmethod
    def _raise_error(response: httpx.Response) -> None:
        payload: dict[str, Any] = {}
        try:
            payload = response.json()
        except Exception:
            pass
        error = payload.get("error", {})
        raise FacebookGraphAPIError(
            error.get("message", f"Facebook API request failed with status {response.status_code}."),
            code=error.get("code"),
            subcode=error.get("error_subcode"),
            status_code=response.status_code,
            payload=payload,
        )
