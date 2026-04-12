def _register_and_create_account(client, email: str, slug: str = "ai-acme"):
    session = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Owner"},
    ).json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    account = client.post(
        "/api/v1/accounts",
        json={"name": "AI Acme", "slug": slug},
        headers=headers,
    ).json()
    headers["X-Account-ID"] = str(account["id"])
    return headers, account


def test_ai_agent_prompt_resolution_and_knowledge_crud(client):
    headers, _ = _register_and_create_account(client, "owner-ai@example.com")

    connection = client.post(
        "/api/v1/platform-connections",
        json={"platform_type": "facebook_page", "name": "Support Page"},
        headers=headers,
    ).json()

    agent_response = client.post(
        "/api/v1/ai/agents",
        json={
            "name": "Support Agent",
            "business_type": "ecommerce",
            "platform_connection_id": connection["id"],
            "status": "active",
            "behavior_json": {"tone": "helpful"},
        },
        headers=headers,
    )
    assert agent_response.status_code == 201
    agent = agent_response.json()

    account_prompt = client.post(
        "/api/v1/ai/prompts",
        json={
            "title": "Default inbox",
            "content": "Use the account default inbox voice.",
            "prompt_type": "inbox_reply",
        },
        headers=headers,
    )
    assert account_prompt.status_code == 201

    connection_prompt = client.post(
        "/api/v1/ai/prompts",
        json={
            "title": "Connection inbox",
            "content": "Use the page-specific inbox voice.",
            "prompt_type": "inbox_reply",
            "platform_connection_id": connection["id"],
        },
        headers=headers,
    )
    assert connection_prompt.status_code == 201

    agent_prompt = client.post(
        "/api/v1/ai/prompts",
        json={
            "title": "Agent inbox",
            "content": "Use the agent-specific inbox voice.",
            "prompt_type": "inbox_reply",
            "ai_agent_id": agent["id"],
        },
        headers=headers,
    )
    assert agent_prompt.status_code == 201
    assert agent_prompt.json()["version"] == 1

    second_agent_prompt = client.post(
        "/api/v1/ai/prompts",
        json={
            "title": "Agent inbox v2",
            "content": "Use the newest agent inbox voice.",
            "prompt_type": "inbox_reply",
            "ai_agent_id": agent["id"],
        },
        headers=headers,
    )
    assert second_agent_prompt.status_code == 201
    assert second_agent_prompt.json()["version"] == 2

    resolution_response = client.get(
        f"/api/v1/ai/prompts/resolve/current?ai_agent_id={agent['id']}&platform_connection_id={connection['id']}",
        headers=headers,
    )
    assert resolution_response.status_code == 200
    inbox_resolution = next(item for item in resolution_response.json() if item["prompt_type"] == "inbox_reply")
    assert inbox_resolution["source_scope"] == "agent-specific"
    assert inbox_resolution["prompt"]["title"] == "Agent inbox v2"

    knowledge_response = client.post(
        "/api/v1/ai/knowledge-sources",
        json={
            "ai_agent_id": agent["id"],
            "title": "Shipping policy",
            "source_type": "file",
            "status": "ready",
            "description": "Policy PDF upload",
            "file_metadata": {
                "file_name": "shipping-policy.pdf",
                "file_size": 1024,
                "mime_type": "application/pdf",
                "storage_key": "knowledge/shipping-policy.pdf",
            },
            "metadata_json": {"category": "shipping"},
        },
        headers=headers,
    )
    assert knowledge_response.status_code == 201
    assert knowledge_response.json()["file_name"] == "shipping-policy.pdf"

    faq_response = client.post(
        "/api/v1/ai/faq",
        json={
            "ai_agent_id": agent["id"],
            "question": "Do you ship internationally?",
            "answer": "Yes, we ship to more than 40 countries.",
            "tags_json": ["shipping", "international"],
        },
        headers=headers,
    )
    assert faq_response.status_code == 201

    overview_response = client.get(f"/api/v1/ai/agents/{agent['id']}", headers=headers)
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["prompt_count"] == 2
    assert overview["knowledge_source_count"] == 1
    assert overview["faq_count"] == 1


def test_admin_can_read_and_manage_ai_configuration(client):
    owner_headers, account = _register_and_create_account(client, "owner-ai-two@example.com", slug="ai-acme-two")
    key_response = client.post(
        "/api/v1/accounts/current/onboarding-keys",
        json={"role": "admin", "max_uses": 1, "invited_email": "admin-ai@example.com"},
        headers=owner_headers,
    )
    onboarding_key = key_response.json()["key"]

    admin_session = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin-ai@example.com",
            "password": "password123",
            "full_name": "Admin",
            "onboarding_key": onboarding_key,
        },
    ).json()
    admin_headers = {
        "Authorization": f"Bearer {admin_session['access_token']}",
        "X-Account-ID": str(account["id"]),
    }

    list_response = client.get("/api/v1/ai/agents", headers=admin_headers)
    assert list_response.status_code == 200

    create_response = client.post(
        "/api/v1/ai/agents",
        json={"name": "Restricted Agent", "status": "active"},
        headers=admin_headers,
    )
    assert create_response.status_code == 201
