from datetime import UTC, datetime, timedelta

from conftest import TestingSessionLocal

from app.models.automation_workflow import AutomationWorkflow
from app.models.conversation import Conversation
from app.models.enums import (
    AutomationActionType,
    AutomationTriggerType,
    AutomationWorkflowStatus,
    CommentStatus,
    ConversationStatus,
    MessageDirection,
    PlatformType,
    SyncJobType,
    WebhookEventSource,
    WebhookEventStatus,
)
from app.models.facebook_comment import FacebookComment
from app.models.message import Message
from app.models.sync_job import SyncJob
from app.models.webhook_event import WebhookEvent
from app.services.automation_workflow_service import AutomationWorkflowService
from app.services.webhook_processing_service import WebhookProcessingService


def seed_account_and_connection(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "automation@example.com",
            "password": "supersecret123",
            "full_name": "Automation Owner",
        },
    )
    token = register_response.json()["access_token"]
    account_response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Automation Co", "slug": "automation-co"},
    )
    account_id = account_response.json()["id"]
    connection_response = client.post(
        "/api/v1/platform-connections",
        headers={"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)},
        json={"platform_type": "whatsapp", "name": "WhatsApp", "external_id": "wa-phone-1"},
    )
    connection_id = connection_response.json()["id"]
    return token, account_id, connection_id


def test_automation_workflow_crud_and_run_endpoint(client):
    token, account_id, connection_id = seed_account_and_connection(client)
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)}

    create_response = client.post(
        "/api/v1/automation/workflows",
        headers=headers,
        json={
            "name": "Welcome replies",
            "status": "active",
            "trigger_type": "inbox_message_received",
            "action_type": "generate_inbox_reply",
            "platform_connection_id": connection_id,
            "delay_seconds": 30,
            "trigger_filters": {"include_keywords": ["price"]},
            "action_config": {"instructions": "Answer with pricing basics.", "send_now": False},
        },
    )
    assert create_response.status_code == 201
    workflow_id = create_response.json()["id"]

    list_response = client.get("/api/v1/automation/workflows", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    update_response = client.put(
        f"/api/v1/automation/workflows/{workflow_id}",
        headers=headers,
        json={"delay_seconds": 90, "description": "Updated workflow"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["delay_seconds"] == 90

    run_response = client.post(f"/api/v1/automation/workflows/{workflow_id}/run", headers=headers)
    assert run_response.status_code == 200
    assert run_response.json()["sync_job_id"] > 0


def test_inbound_webhook_queues_automation_job_and_generates_reply(client):
    _, account_id, connection_id = seed_account_and_connection(client)

    with TestingSessionLocal() as db:
        workflow = AutomationWorkflow(
            account_id=account_id,
            platform_connection_id=connection_id,
            name="Auto reply",
            status=AutomationWorkflowStatus.ACTIVE,
            trigger_type=AutomationTriggerType.INBOX_MESSAGE_RECEIVED,
            action_type=AutomationActionType.GENERATE_INBOX_REPLY,
            delay_seconds=0,
            trigger_filters_json={"include_keywords": ["price"]},
            action_config_json={"instructions": "Share pricing helpfully.", "send_now": False},
            last_result_json={},
        )
        db.add(workflow)
        db.flush()

        event = WebhookEvent(
            account_id=account_id,
            platform_connection_id=connection_id,
            platform_type=PlatformType.WHATSAPP,
            source=WebhookEventSource.WHATSAPP,
            status=WebhookEventStatus.PENDING,
            event_type="message",
            event_key="wa:event:1",
            received_at=datetime.now(UTC),
            payload_json={
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "id": "wamid-1",
                                            "from": "8801555000111",
                                            "timestamp": str(int(datetime.now(UTC).timestamp())),
                                            "text": {"body": "Need price details today"},
                                            "type": "text",
                                        }
                                    ],
                                    "contacts": [{"profile": {"name": "Buyer"}, "wa_id": "8801555000111"}],
                                    "metadata": {"phone_number_id": "wa-phone-1"},
                                }
                            }
                        ]
                    }
                ]
            },
            headers_json={},
            metadata_json={},
        )
        db.add(event)
        db.commit()
        event_id = event.id
        workflow_id = workflow.id

        service = WebhookProcessingService(db)
        result = service.process_event(event_id)
        assert result["status"] == "processed"

        jobs = db.query(SyncJob).all()
        assert any(job.job_type == SyncJobType.AUTOMATION_RULE_EXECUTION for job in jobs)
        assert not any(job.job_type == SyncJobType.AI_REPLY_GENERATION for job in jobs)

        job = next(job for job in jobs if job.job_type == SyncJobType.AUTOMATION_RULE_EXECUTION)
        execution_result = AutomationWorkflowService(db).execute_job(workflow_id=workflow_id, payload_json=job.payload_json)
        assert execution_result["status"] == "generated"

        outbound_messages = db.query(Message).filter(Message.direction == MessageDirection.OUTBOUND).all()
        assert len(outbound_messages) == 1


def test_scheduled_workflow_scan_creates_sync_job(client):
    _, account_id, connection_id = seed_account_and_connection(client)

    with TestingSessionLocal() as db:
        workflow = AutomationWorkflow(
            account_id=account_id,
            platform_connection_id=connection_id,
            name="Daily post draft",
            status=AutomationWorkflowStatus.ACTIVE,
            trigger_type=AutomationTriggerType.SCHEDULED_DAILY,
            action_type=AutomationActionType.GENERATE_POST_DRAFT,
            delay_seconds=0,
            trigger_filters_json={},
            action_config_json={"title_hint": "Daily roundup"},
            schedule_timezone="UTC",
            schedule_local_time="00:15",
            next_run_at=datetime.now(UTC) - timedelta(minutes=1),
            last_result_json={},
        )
        db.add(workflow)
        db.commit()

        created = AutomationWorkflowService(db).queue_due_scheduled_workflows()
        assert created == 1

        jobs = db.query(SyncJob).filter(SyncJob.job_type == SyncJobType.AUTOMATION_RULE_EXECUTION).all()
        assert len(jobs) == 1
        db.refresh(workflow)
        assert workflow.next_run_at is not None
        assert workflow.next_run_at.timestamp() > datetime.now(UTC).timestamp()


def test_abusive_inbound_message_is_escalated_and_not_queued_for_ai(client):
    _, account_id, connection_id = seed_account_and_connection(client)

    with TestingSessionLocal() as db:
        event = WebhookEvent(
            account_id=account_id,
            platform_connection_id=connection_id,
            platform_type=PlatformType.WHATSAPP,
            source=WebhookEventSource.WHATSAPP,
            status=WebhookEventStatus.PENDING,
            event_type="message",
            event_key="wa:event:abusive-1",
            received_at=datetime.now(UTC),
            payload_json={
                "entry": [
                    {
                        "changes": [
                            {
                                "value": {
                                    "messages": [
                                        {
                                            "id": "wamid-abusive-1",
                                            "from": "8801555000999",
                                            "timestamp": str(int(datetime.now(UTC).timestamp())),
                                            "text": {"body": "You are a bitch and this service is shit"},
                                            "type": "text",
                                        }
                                    ],
                                    "contacts": [{"profile": {"name": "Angry Buyer"}, "wa_id": "8801555000999"}],
                                    "metadata": {"phone_number_id": "wa-phone-1"},
                                }
                            }
                        ]
                    }
                ]
            },
            headers_json={},
            metadata_json={},
        )
        db.add(event)
        db.commit()

        result = WebhookProcessingService(db).process_event(event.id)
        assert result["status"] == "processed"

        conversation = db.query(Conversation).filter(Conversation.account_id == account_id).one()
        assert conversation.status == ConversationStatus.ESCALATED
        assert conversation.metadata_json["moderation"]["flagged"] is True

        jobs = db.query(SyncJob).all()
        assert jobs == []


def test_abusive_facebook_comment_is_flagged_and_not_queued_for_ai(client):
    _, account_id, connection_id = seed_account_and_connection(client)

    with TestingSessionLocal() as db:
        event = WebhookEvent(
            account_id=account_id,
            platform_connection_id=connection_id,
            platform_type=PlatformType.FACEBOOK_PAGE,
            source=WebhookEventSource.FACEBOOK_PAGE,
            status=WebhookEventStatus.PENDING,
            event_type="feed",
            event_key="fb:event:abusive-comment-1",
            received_at=datetime.now(UTC),
            payload_json={
                "object": "page",
                "entry": [
                    {
                        "id": "page_123",
                        "changes": [
                            {
                                "field": "feed",
                                "value": {
                                    "item": "comment",
                                    "comment_id": "comment_abusive_1",
                                    "post_id": "post_123",
                                    "from": {"id": "user_999", "name": "Toxic User"},
                                    "message": "fuck this post, you bastard",
                                    "created_time": int(datetime.now(UTC).timestamp()),
                                },
                            }
                        ],
                    }
                ],
            },
            headers_json={},
            metadata_json={},
        )
        db.add(event)
        db.commit()

        result = WebhookProcessingService(db).process_event(event.id)
        assert result["status"] == "processed"

        comment = db.query(FacebookComment).filter(FacebookComment.account_id == account_id).one()
        assert comment.status == CommentStatus.FLAGGED
        assert comment.flagged_reason is not None
        assert comment.metadata_json["moderation"]["flagged"] is True

        jobs = db.query(SyncJob).all()
        assert jobs == []
