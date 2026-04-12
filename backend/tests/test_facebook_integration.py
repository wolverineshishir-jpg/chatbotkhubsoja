from app.integrations.facebook.client import FacebookGraphAPIClient
from app.integrations.facebook.parsers import FacebookWebhookParser


def _register_and_create_account(client, email: str, slug: str = "acme"):
    session = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Owner"},
    ).json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    account = client.post(
        "/api/v1/accounts",
        json={"name": "Acme", "slug": slug},
        headers=headers,
    ).json()
    headers["X-Account-ID"] = str(account["id"])
    return session, headers, account


def test_facebook_webhook_parser_extracts_messages_and_comments():
    payload = {
        "object": "page",
        "entry": [
            {
                "id": "page_123",
                "messaging": [
                    {
                        "sender": {"id": "user_1"},
                        "recipient": {"id": "page_123"},
                        "timestamp": 1710000000,
                        "message": {"mid": "mid.1", "text": "Hello there"},
                    }
                ],
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "comment_id": "comment_123",
                            "post_id": "post_123",
                            "from": {"id": "user_2", "name": "Jane"},
                            "message": "Nice post",
                            "created_time": 1710001111,
                        },
                    }
                ],
            }
        ],
    }

    parsed = FacebookWebhookParser().parse(payload)

    assert len(parsed.messages) == 1
    assert parsed.messages[0].page_id == "page_123"
    assert parsed.messages[0].message_id == "mid.1"
    assert parsed.messages[0].text == "Hello there"
    assert len(parsed.comments) == 1
    assert parsed.comments[0].comment_id == "comment_123"
    assert parsed.comments[0].message == "Nice post"


def test_manual_facebook_connect_creates_account_scoped_connection(client, monkeypatch):
    _, headers, _ = _register_and_create_account(client, "facebook-owner@example.com", slug="facebook-acme")

    def fake_get_page_profile(self, *, page_id: str, access_token: str):
        return type(
            "Profile",
            (),
            {
                "page_id": page_id,
                "page_name": "Acme Support",
                "category": "Business",
                "followers_count": 125,
                "picture_url": "https://example.com/page.png",
            },
        )()

    monkeypatch.setattr(FacebookGraphAPIClient, "get_page_profile", fake_get_page_profile)

    response = client.post(
        "/api/v1/platform-connections/facebook/manual-connect",
        json={
            "page_id": "page_123",
            "page_access_token": "facebook-page-token-secret",
            "connection_name": "Acme Facebook",
            "user_access_token": "facebook-user-token-secret",
            "webhook_verify_token": "verify-me",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["platform_type"] == "facebook_page"
    assert body["external_id"] == "page_123"
    assert body["name"] == "Acme Facebook"
    assert body["token_hint"].startswith("...")
    assert body["integration_summary"]["provider"] == "facebook"
    assert body["integration_summary"]["connected_via"] == "manual"
    assert body["integration_summary"]["token_status"] == "valid"
    assert "page_access_token" not in str(body)
