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


def test_platform_connection_crud_hides_tokens(client):
    _, headers, _ = _register_and_create_account(client, "owner@example.com")

    create_response = client.post(
        "/api/v1/platform-connections",
        json={
            "platform_type": "facebook_page",
            "name": "Acme Facebook",
            "external_id": "page_123",
            "access_token": "facebook-access-token-secret",
            "refresh_token": "facebook-refresh-token-secret",
            "webhook": {
                "webhook_url": "https://example.com/webhooks/facebook",
                "webhook_secret": "secret-value",
                "webhook_verify_token": "verify-token",
                "webhook_active": True,
            },
            "settings_json": {"reply_mode": "manual"},
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "connected"
    assert created["token_hint"].startswith("...")
    assert "access_token" not in created
    assert created["webhook"]["has_secret"] is True

    list_response = client.get("/api/v1/platform-connections", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    update_response = client.put(
        f"/api/v1/platform-connections/{created['id']}",
        json={"name": "Updated Facebook", "last_error": "Webhook verification failed."},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "error"

    disconnect_response = client.post(
        f"/api/v1/platform-connections/{created['id']}/disconnect",
        headers=headers,
    )
    assert disconnect_response.status_code == 200
    assert disconnect_response.json()["status"] == "disconnected"
    assert disconnect_response.json()["token_hint"] is None


def test_admin_can_manage_platform_connections(client):
    _, owner_headers, account = _register_and_create_account(client, "owner@example.com")
    key_response = client.post(
        "/api/v1/accounts/current/onboarding-keys",
        json={"role": "admin", "max_uses": 1, "invited_email": "admin@example.com"},
        headers=owner_headers,
    )
    onboarding_key = key_response.json()["key"]

    admin_session = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "password123",
            "full_name": "Admin",
            "onboarding_key": onboarding_key,
        },
    ).json()
    admin_headers = {
        "Authorization": f"Bearer {admin_session['access_token']}",
        "X-Account-ID": str(account["id"]),
    }

    create_response = client.post(
        "/api/v1/platform-connections",
        json={"platform_type": "whatsapp", "name": "Support WhatsApp", "external_id": "wa-admin-1"},
        headers=admin_headers,
    )
    assert create_response.status_code == 201


def test_superuser_can_manage_platform_connections_without_membership(client):
    _, owner_headers, account = _register_and_create_account(client, "owner@example.com")

    super_session = client.post(
        "/api/v1/auth/register",
        json={"email": "super@example.com", "password": "password123", "full_name": "Super User"},
    ).json()

    from conftest import TestingSessionLocal
    from app.models.user import User

    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == "super@example.com").one()
        user.is_superuser = True
        db.commit()

    super_headers = {
        "Authorization": f"Bearer {super_session['access_token']}",
        "X-Account-ID": str(account["id"]),
    }
    create_response = client.post(
        "/api/v1/platform-connections",
        json={"platform_type": "whatsapp", "name": "Support WhatsApp", "external_id": "wa-1"},
        headers=super_headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "Support WhatsApp"
