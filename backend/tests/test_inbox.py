from app.models.conversation import Conversation
from app.models.enums import ConversationStatus, MessageDeliveryStatus, MessageDirection, PlatformType, SenderType
from app.models.message import Message
from conftest import TestingSessionLocal


def create_seeded_conversation(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "supersecret123",
            "full_name": "Owner",
        },
    )
    token = register_response.json()["access_token"]
    account_response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Acme", "slug": "acme"},
    )
    account_id = account_response.json()["id"]
    connection_response = client.post(
        "/api/v1/platform-connections",
        headers={"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)},
        json={"platform_type": "facebook_page", "name": "Main Page", "external_id": "page-1"},
    )
    connection_id = connection_response.json()["id"]

    with TestingSessionLocal() as db:
        conversation = Conversation(
            account_id=account_id,
            platform_connection_id=connection_id,
            platform_type=PlatformType.FACEBOOK_PAGE,
            status=ConversationStatus.OPEN,
            external_thread_id="thread-123",
            customer_external_id="customer-456",
            customer_name="Jane Customer",
            latest_message_preview="Need help",
            metadata_json={},
        )
        db.add(conversation)
        db.flush()
        db.add(
            Message(
                account_id=account_id,
                conversation_id=conversation.id,
                sender_type=SenderType.CUSTOMER,
                direction=MessageDirection.INBOUND,
                delivery_status=MessageDeliveryStatus.DELIVERED,
                sender_name="Jane Customer",
                sender_external_id="customer-456",
                content="Need help with my order",
                metadata_json={},
            )
        )
        db.commit()
        conversation_id = conversation.id

    return token, account_id, conversation_id


def test_list_and_detail_conversations(client):
    token, account_id, conversation_id = create_seeded_conversation(client)
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)}

    list_response = client.get("/api/v1/inbox/conversations", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["customer_name"] == "Jane Customer"

    detail_response = client.get(f"/api/v1/inbox/conversations/{conversation_id}", headers=headers)
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == conversation_id
    assert detail_payload["messages_total"] == 1
    assert detail_payload["messages"][0]["sender_type"] == "customer"


def test_assign_update_status_and_reply(client):
    token, account_id, conversation_id = create_seeded_conversation(client)
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)}

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me_response.json()["id"]

    assign_response = client.post(
        f"/api/v1/inbox/conversations/{conversation_id}/assign",
        headers=headers,
        json={"assignee_user_id": user_id},
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["status"] == "assigned"

    status_response = client.patch(
        f"/api/v1/inbox/conversations/{conversation_id}/status",
        headers=headers,
        json={"status": "escalated"},
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "escalated"

    reply_response = client.post(
        f"/api/v1/inbox/conversations/{conversation_id}/reply",
        headers=headers,
        json={"content": "We are checking this now.", "sender_type": "human_admin"},
    )
    assert reply_response.status_code == 201
    reply_payload = reply_response.json()
    assert reply_payload["direction"] == "outbound"
    assert reply_payload["delivery_status"] in {"queued", "sent", "failed"}
