from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx

from app.core.config import get_settings
from app.integrations.whatsapp.schemas import WhatsAppPhoneNumberProfile


class WhatsAppCloudAPIError(Exception):
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


class WhatsAppCloudAPIClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = f"{self.settings.whatsapp_graph_api_base_url}/{self.settings.whatsapp_graph_api_version}"

    def get_phone_number_profile(self, *, phone_number_id: str, access_token: str) -> WhatsAppPhoneNumberProfile:
        data = self._request(
            "GET",
            f"/{phone_number_id}",
            access_token=access_token,
            params={"fields": "id,display_phone_number,verified_name,quality_rating"},
        )
        return WhatsAppPhoneNumberProfile(
            phone_number_id=str(data.get("id") or phone_number_id),
            display_phone_number=data.get("display_phone_number"),
            verified_name=data.get("verified_name"),
            quality_rating=data.get("quality_rating"),
        )

    def send_text_message(
        self,
        *,
        phone_number_id: str,
        access_token: str,
        recipient_phone: str,
        text: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/{phone_number_id}/messages",
            access_token=access_token,
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient_phone,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            },
        )

    def verify_webhook_signature(self, *, raw_body: bytes, signature_header: str | None) -> bool:
        if not self.settings.whatsapp_verify_signature:
            return True
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        secret = self.settings.facebook_app_secret.get_secret_value()
        if not secret:
            return False
        expected = hmac.new(secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature_header.split("=", 1)[1], expected)

    def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {access_token}"}
        with httpx.Client(timeout=self.settings.whatsapp_http_timeout_seconds) as client:
            response = client.request(method, url, params=params or None, json=json, headers=headers)
        if response.status_code >= 400:
            self._raise_error(response)

        data = response.json()
        if "error" in data:
            error = data["error"]
            raise WhatsAppCloudAPIError(
                error.get("message", "WhatsApp API request failed."),
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
        raise WhatsAppCloudAPIError(
            error.get("message", f"WhatsApp API request failed with status {response.status_code}."),
            code=error.get("code"),
            subcode=error.get("error_subcode"),
            status_code=response.status_code,
            payload=payload,
        )
