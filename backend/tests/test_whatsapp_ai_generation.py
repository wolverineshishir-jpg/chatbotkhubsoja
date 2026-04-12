from app.integrations.whatsapp.schemas import WhatsAppPhoneNumberProfile
from app.core.config import get_settings
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.enums import (
    ConversationStatus,
    MessageDeliveryStatus,
    MessageDirection,
    PlatformType,
    SenderType,
)
from app.models.message import Message


def _register_and_create_account(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "password123",
            "full_name": "Owner User",
        },
    )
    token = register_response.json()["access_token"]
    account_response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Acme", "slug": "acme"},
    )
    account = account_response.json()
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account["id"])}
    return headers, account


def test_whatsapp_manual_connect_creates_connection(client, monkeypatch):
    headers, _ = _register_and_create_account(client)

    def fake_profile(self, *, phone_number_id: str, access_token: str):
        assert phone_number_id == "1234567890"
        assert access_token == "whatsapp-token-secret"
        return WhatsAppPhoneNumberProfile(
            phone_number_id=phone_number_id,
            display_phone_number="+88010000000",
            verified_name="Automation Support",
            quality_rating="GREEN",
        )

    monkeypatch.setattr("app.integrations.whatsapp.client.WhatsAppCloudAPIClient.get_phone_number_profile", fake_profile)

    response = client.post(
        "/api/v1/platform-connections/whatsapp/manual-connect",
        headers=headers,
        json={
            "phone_number_id": "1234567890",
            "access_token": "whatsapp-token-secret",
            "connection_name": "Primary WhatsApp",
            "webhook_verify_token": "wa-verify",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["platform_type"] == "whatsapp"
    assert body["integration_summary"]["provider"] == "whatsapp"
    assert body["integration_summary"]["token_status"] == "valid"


def test_inbox_generation_endpoint_returns_draft(client):
    headers, account = _register_and_create_account(client)
    connection_response = client.post(
        "/api/v1/platform-connections",
        headers=headers,
        json={"platform_type": "whatsapp", "name": "WA Inbox", "external_id": "wa-phone-id"},
    )
    connection_id = connection_response.json()["id"]

    override_get_db = client.app.dependency_overrides[get_db]
    db_generator = override_get_db()
    db = next(db_generator)
    try:
        conversation = Conversation(
            account_id=account["id"],
            platform_connection_id=connection_id,
            platform_type=PlatformType.WHATSAPP,
            status=ConversationStatus.OPEN,
            customer_external_id="8801710000000",
            customer_name="Customer",
            external_thread_id="wa-phone-id",
            metadata_json={},
        )
        db.add(conversation)
        db.flush()
        db.add(
            Message(
                account_id=account["id"],
                conversation_id=conversation.id,
                sender_type=SenderType.CUSTOMER,
                direction=MessageDirection.INBOUND,
                delivery_status=MessageDeliveryStatus.DELIVERED,
                sender_name="Customer",
                sender_external_id="8801710000000",
                content="Can you share pricing details?",
                metadata_json={},
            )
        )
        db.commit()
        conversation_id = conversation.id
    finally:
        db_generator.close()

    response = client.post(
        "/api/v1/ai/generation/inbox-reply",
        headers=headers,
        json={"conversation_id": conversation_id, "persist_draft": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"]
    assert body["total_tokens"] > 0
    assert body["platform_connection_id"] == connection_id


def test_inbox_generation_uses_nano_by_default_for_openai(client, monkeypatch):
    headers, account = _register_and_create_account(client)
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "openai")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "gpt-5.4-nano")
    monkeypatch.setenv("OPENAI_REPLY_PRIMARY_MODEL", "gpt-5.4-nano")
    monkeypatch.setenv("OPENAI_REPLY_FALLBACK_MODEL", "gpt-5.4-mini")
    get_settings.cache_clear()

    calls: list[str] = []

    def fake_generate(self, *, system_prompt, user_prompt, max_output_tokens=512, temperature=0.2, model_name=None):
        del self, system_prompt, user_prompt, max_output_tokens, temperature
        calls.append(model_name or "")
        return type("Result", (), {
            "content": '{"reply_text":"আমরা pricing details শেয়ার করতে পারি। আপনার প্রয়োজন বললে আমি package suggest করব।","safe_to_send":true,"confidence":0.86,"escalate_to_mini":false,"detected_tone":"neutral","detected_intent":"pricing","notes":"ok"}',
            "provider": "openai",
            "model_name": model_name or "gpt-5.4-nano",
            "prompt_tokens": 10,
            "completion_tokens": 12,
            "total_tokens": 22,
        })()

    monkeypatch.setattr("app.services.ai.providers.openai_provider.OpenAIProvider.generate", fake_generate)

    connection_response = client.post(
        "/api/v1/platform-connections",
        headers=headers,
        json={"platform_type": "whatsapp", "name": "WA Inbox", "external_id": "wa-phone-id"},
    )
    connection_id = connection_response.json()["id"]

    override_get_db = client.app.dependency_overrides[get_db]
    db_generator = override_get_db()
    db = next(db_generator)
    try:
        conversation = Conversation(
            account_id=account["id"],
            platform_connection_id=connection_id,
            platform_type=PlatformType.WHATSAPP,
            status=ConversationStatus.OPEN,
            customer_external_id="8801710000000",
            customer_name="Customer",
            external_thread_id="wa-phone-id",
            metadata_json={},
        )
        db.add(conversation)
        db.flush()
        db.add(
            Message(
                account_id=account["id"],
                conversation_id=conversation.id,
                sender_type=SenderType.CUSTOMER,
                direction=MessageDirection.INBOUND,
                delivery_status=MessageDeliveryStatus.DELIVERED,
                sender_name="Customer",
                sender_external_id="8801710000000",
                content="Can you share pricing details?",
                metadata_json={},
            )
        )
        db.commit()
        conversation_id = conversation.id
    finally:
        db_generator.close()

    response = client.post(
        "/api/v1/ai/generation/inbox-reply",
        headers=headers,
        json={"conversation_id": conversation_id, "persist_draft": False},
    )
    get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["content"].startswith("আমরা pricing details")
    assert body["model_name"] == "gpt-5.4-nano"
    assert calls == ["gpt-5.4-nano"]


def test_inbox_generation_falls_back_to_mini_for_angry_low_confidence_context(client, monkeypatch):
    headers, account = _register_and_create_account(client)
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "openai")
    monkeypatch.setenv("LLM_DEFAULT_MODEL", "gpt-5.4-nano")
    monkeypatch.setenv("OPENAI_REPLY_PRIMARY_MODEL", "gpt-5.4-nano")
    monkeypatch.setenv("OPENAI_REPLY_FALLBACK_MODEL", "gpt-5.4-mini")
    get_settings.cache_clear()

    calls: list[str] = []

    def fake_generate(self, *, system_prompt, user_prompt, max_output_tokens=512, temperature=0.2, model_name=None):
        del self, system_prompt, user_prompt, max_output_tokens, temperature
        calls.append(model_name or "")
        if model_name == "gpt-5.4-nano":
            return type("Result", (), {
                "content": '{"reply_text":"We are checking this issue.","safe_to_send":false,"confidence":0.32,"escalate_to_mini":true,"detected_tone":"angry","detected_intent":"complaint","notes":"needs escalation"}',
                "provider": "openai",
                "model_name": "gpt-5.4-nano",
                "prompt_tokens": 11,
                "completion_tokens": 8,
                "total_tokens": 19,
            })()
        return type("Result", (), {
            "content": '{"reply_text":"আপনার অসুবিধার জন্য দুঃখিত। আমরা বিষয়টি দ্রুত দেখে আপনাকে update দেব।","safe_to_send":true,"confidence":0.92,"escalate_to_mini":false,"detected_tone":"empathetic","detected_intent":"complaint_resolution","notes":"safe"}',
            "provider": "openai",
            "model_name": "gpt-5.4-mini",
            "prompt_tokens": 15,
            "completion_tokens": 14,
            "total_tokens": 29,
        })()

    monkeypatch.setattr("app.services.ai.providers.openai_provider.OpenAIProvider.generate", fake_generate)

    connection_response = client.post(
        "/api/v1/platform-connections",
        headers=headers,
        json={"platform_type": "whatsapp", "name": "WA Inbox", "external_id": "wa-phone-id"},
    )
    connection_id = connection_response.json()["id"]

    override_get_db = client.app.dependency_overrides[get_db]
    db_generator = override_get_db()
    db = next(db_generator)
    try:
        conversation = Conversation(
            account_id=account["id"],
            platform_connection_id=connection_id,
            platform_type=PlatformType.WHATSAPP,
            status=ConversationStatus.OPEN,
            customer_external_id="8801710000000",
            customer_name="Customer",
            external_thread_id="wa-phone-id",
            metadata_json={},
        )
        db.add(conversation)
        db.flush()
        db.add(
            Message(
                account_id=account["id"],
                conversation_id=conversation.id,
                sender_type=SenderType.CUSTOMER,
                direction=MessageDirection.INBOUND,
                delivery_status=MessageDeliveryStatus.DELIVERED,
                sender_name="Customer",
                sender_external_id="8801710000000",
                content="I am very upset. This is terrible service and I want a refund now.",
                metadata_json={},
            )
        )
        db.commit()
        conversation_id = conversation.id
    finally:
        db_generator.close()

    response = client.post(
        "/api/v1/ai/generation/inbox-reply",
        headers=headers,
        json={"conversation_id": conversation_id, "persist_draft": False},
    )
    get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert body["content"].startswith("আপনার অসুবিধার জন্য দুঃখিত")
    assert body["model_name"] == "gpt-5.4-mini"
    assert body["requires_approval"] is True
    assert body["total_tokens"] == 48
    assert calls == ["gpt-5.4-nano", "gpt-5.4-mini"]
