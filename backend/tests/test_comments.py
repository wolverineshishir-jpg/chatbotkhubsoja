from conftest import TestingSessionLocal

from app.models.enums import CommentReplyStatus, CommentStatus, PlatformType, SenderType
from app.models.facebook_comment import FacebookComment
from app.models.facebook_comment_reply import FacebookCommentReply


def create_seeded_comment(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "moderator@example.com",
            "password": "supersecret123",
            "full_name": "Moderator",
        },
    )
    token = register_response.json()["access_token"]
    account_response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Comments Co", "slug": "comments-co"},
    )
    account_id = account_response.json()["id"]
    connection_response = client.post(
        "/api/v1/platform-connections",
        headers={"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)},
        json={"platform_type": "facebook_page", "name": "Facebook", "external_id": "page-2"},
    )
    connection_id = connection_response.json()["id"]

    with TestingSessionLocal() as db:
        comment = FacebookComment(
            account_id=account_id,
            platform_connection_id=connection_id,
            platform_type=PlatformType.FACEBOOK_PAGE,
            status=CommentStatus.PENDING,
            post_external_id="post-123",
            post_title="Launch post",
            external_comment_id="comment-555",
            commenter_external_id="user-555",
            commenter_name="Alex Reader",
            comment_text="Can you share pricing details?",
            metadata_json={"source": "seed"},
        )
        db.add(comment)
        db.flush()
        db.add(
            FacebookCommentReply(
                account_id=account_id,
                comment_id=comment.id,
                sender_type=SenderType.LLM_BOT,
                reply_status=CommentReplyStatus.DRAFT,
                content="Thanks for your interest. Sending details shortly.",
                metadata_json={"draft": True},
            )
        )
        db.commit()
        comment_id = comment.id

    return token, account_id, comment_id


def test_list_and_detail_comments(client):
    token, account_id, comment_id = create_seeded_comment(client)
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)}

    list_response = client.get("/api/v1/comments", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["commenter_name"] == "Alex Reader"

    detail_response = client.get(f"/api/v1/comments/{comment_id}", headers=headers)
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == comment_id
    assert detail_payload["replies"][0]["reply_status"] == "draft"


def test_update_comment_status_and_create_reply(client):
    token, account_id, comment_id = create_seeded_comment(client)
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)}

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/comments/{comment_id}/status",
        headers=headers,
        json={
            "status": "flagged",
            "assignee_user_id": user_id,
            "flagged_reason": "Possible spam follow-up required",
        },
    )
    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["status"] == "flagged"
    assert payload["assigned_to"]["user_id"] == user_id

    reply_response = client.post(
        f"/api/v1/comments/{comment_id}/replies",
        headers=headers,
        json={
            "content": "Happy to help. Please check our pricing page.",
            "sender_type": "human_admin",
            "send_now": True,
        },
    )
    assert reply_response.status_code == 201
    reply_payload = reply_response.json()
    assert reply_payload["sender_type"] == "human_admin"
    assert reply_payload["reply_status"] in {"queued", "sent", "failed"}
