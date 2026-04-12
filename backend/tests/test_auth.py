from app.core.config import get_settings


OWNER_EMAIL = get_settings().owner_email
OWNER_PASSWORD = get_settings().owner_password.get_secret_value()


def _login_owner(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
    )
    assert response.status_code == 200
    return response.json()


def _create_super_admin(client, owner_access_token: str):
    response = client.post(
        "/api/v1/users/super-admins",
        json={
            "email": "superadmin@example.com",
            "password": "SuperAdmin123!",
            "full_name": "Workspace Super Admin",
            "status": "active",
            "account_name": "Acme",
            "account_slug": "acme",
            "permissions": [
                "feature:whatsapp_inbox",
                "feature:facebook_inbox",
                "feature:facebook_comments",
                "feature:facebook_posts",
            ],
        },
        headers={"Authorization": f"Bearer {owner_access_token}"},
    )
    assert response.status_code == 201
    return response.json()


def test_owner_bootstrap_login_and_registration_returns_session(client):
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["user"]["user_role"] == "owner"
    assert body["user"]["email"] == OWNER_EMAIL

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "someone@example.com", "password": "Password123!", "full_name": "Someone"},
    )
    assert register_response.status_code == 200
    register_body = register_response.json()
    assert register_body["user"]["email"] == "someone@example.com"
    assert register_body["user"]["user_role"] == "admin"


def test_owner_creates_super_admin_and_super_admin_creates_admin(client):
    owner = _login_owner(client)
    super_admin = _create_super_admin(client, owner["access_token"])

    super_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@example.com", "password": "SuperAdmin123!"},
    )
    assert super_login_response.status_code == 200
    super_session = super_login_response.json()
    assert super_session["user"]["user_role"] == "superAdmin"

    admin_create_response = client.post(
        "/api/v1/users/admins",
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123!",
            "full_name": "Support Admin",
            "status": "active",
            "permissions": ["team:read", "reports:read", "inbox:read"],
        },
        headers={
            "Authorization": f"Bearer {super_session['access_token']}",
            "X-Account-ID": str(super_admin["account_id"]),
        },
    )
    assert admin_create_response.status_code == 201
    admin_body = admin_create_response.json()
    assert admin_body["user_role"] == "admin"
    assert admin_body["permissions"] == ["inbox:read", "reports:read", "team:read"]


def test_owner_disabling_super_admin_cascades_to_managed_admins(client):
    owner = _login_owner(client)
    super_admin = _create_super_admin(client, owner["access_token"])

    super_session = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@example.com", "password": "SuperAdmin123!"},
    ).json()

    admin_response = client.post(
        "/api/v1/users/admins",
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123!",
            "full_name": "Support Admin",
            "status": "active",
            "permissions": ["team:read", "reports:read"],
        },
        headers={
            "Authorization": f"Bearer {super_session['access_token']}",
            "X-Account-ID": str(super_admin["account_id"]),
        },
    )
    assert admin_response.status_code == 201

    disable_response = client.patch(
        f"/api/v1/users/super-admins/{super_admin['id']}",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {owner['access_token']}"},
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["status"] == "disabled"

    super_login = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@example.com", "password": "SuperAdmin123!"},
    )
    assert super_login.status_code == 403

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPassword123!"},
    )
    assert admin_login.status_code == 403


def test_change_password_rotates_session_for_super_admin(client):
    owner = _login_owner(client)
    _create_super_admin(client, owner["access_token"])

    super_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@example.com", "password": "SuperAdmin123!"},
    )
    assert super_login_response.status_code == 200
    session = super_login_response.json()

    change_password_response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "SuperAdmin123!", "new_password": "NewSuperAdmin123!"},
        headers={"Authorization": f"Bearer {session['access_token']}"},
    )
    assert change_password_response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@example.com", "password": "SuperAdmin123!"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@example.com", "password": "NewSuperAdmin123!"},
    )
    assert new_login.status_code == 200
