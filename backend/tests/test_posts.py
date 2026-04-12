from datetime import UTC, datetime, timedelta

from conftest import TestingSessionLocal

from app.models.ai_agent import AIAgent
from app.models.ai_prompt import AIPrompt
from app.models.enums import AIAgentStatus, PlatformType, PostGeneratedBy, PostStatus, PromptType
from app.models.social_post import SocialPost


def create_seeded_post(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "publisher@example.com",
            "password": "supersecret123",
            "full_name": "Publisher",
        },
    )
    token = register_response.json()["access_token"]
    account_response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Posts Co", "slug": "posts-co"},
    )
    account_id = account_response.json()["id"]
    connection_response = client.post(
        "/api/v1/platform-connections",
        headers={"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)},
        json={"platform_type": "facebook_page", "name": "FB Page", "external_id": "fb-page-99"},
    )
    connection_id = connection_response.json()["id"]

    with TestingSessionLocal() as db:
        agent = AIAgent(
            account_id=account_id,
            platform_connection_id=connection_id,
            name="Content Agent",
            status=AIAgentStatus.ACTIVE,
            settings_json={},
            behavior_json={},
        )
        db.add(agent)
        db.flush()
        prompt = AIPrompt(
            account_id=account_id,
            ai_agent_id=agent.id,
            platform_connection_id=connection_id,
            prompt_type=PromptType.POST_GENERATION,
            title="Post prompt",
            content="Generate a post",
            version=1,
            is_active=True,
        )
        db.add(prompt)
        db.flush()
        post = SocialPost(
            account_id=account_id,
            platform_connection_id=connection_id,
            ai_agent_id=agent.id,
            ai_prompt_id=prompt.id,
            platform_type=PlatformType.FACEBOOK_PAGE,
            status=PostStatus.DRAFT,
            generated_by=PostGeneratedBy.HUMAN_ADMIN,
            title="Launch update",
            content="We are launching today.",
            media_urls=["https://example.com/image.jpg"],
            requires_approval=True,
            metadata_json={},
        )
        db.add(post)
        db.commit()
        post_id = post.id
        agent_id = agent.id
        prompt_id = prompt.id

    return token, account_id, connection_id, agent_id, prompt_id, post_id


def test_list_and_get_posts(client):
    token, account_id, _, _, _, post_id = create_seeded_post(client)
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)}

    list_response = client.get("/api/v1/posts", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    detail_response = client.get(f"/api/v1/posts/{post_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Launch update"


def test_post_workflow_endpoints(client):
    token, account_id, connection_id, agent_id, prompt_id, post_id = create_seeded_post(client)
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)}

    approve_response = client.post(
        f"/api/v1/posts/{post_id}/approve",
        headers=headers,
        json={"note": "Looks good"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    schedule_response = client.post(
        f"/api/v1/posts/{post_id}/schedule",
        headers=headers,
        json={"scheduled_for": (datetime.now(UTC) + timedelta(hours=2)).isoformat()},
    )
    assert schedule_response.status_code == 200
    assert schedule_response.json()["status"] == "scheduled"

    create_response = client.post(
        "/api/v1/posts",
        headers=headers,
        json={
            "title": "AI post",
            "content": "Generated campaign update",
            "platform_connection_id": connection_id,
            "ai_agent_id": agent_id,
            "ai_prompt_id": prompt_id,
            "generated_by": "llm_bot",
            "is_llm_generated": True,
            "requires_approval": False,
            "media_urls": [],
            "metadata_json": {"campaign": "spring"},
        },
    )
    assert create_response.status_code == 201
    created_post_id = create_response.json()["id"]

    publish_response = client.post(f"/api/v1/posts/{created_post_id}/publish-now", headers=headers)
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] in {"scheduled", "published", "failed"}

    reject_response = client.post(
        f"/api/v1/posts/{post_id}/reject",
        headers=headers,
        json={"reason": "Need new artwork"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"
