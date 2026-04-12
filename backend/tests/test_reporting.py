def create_reporting_session(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "reports@example.com",
            "password": "StrongPassword123!",
            "full_name": "Reports Admin",
        },
    )
    token = register_response.json()["access_token"]

    account_response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Reports Account", "slug": "reports-account"},
    )
    account_id = account_response.json()["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account_id)}

    client.post(
        "/api/v1/observability/action-usage-logs",
        headers=headers,
        json={
            "action_type": "ai_reply_generation",
            "quantity": 2,
            "tokens_consumed": 300,
            "estimated_cost": "1.25",
            "reference_type": "sync_job",
            "reference_id": "job-1",
        },
    )
    client.post(
        "/api/v1/observability/llm-token-usage",
        headers=headers,
        json={
            "provider": "openai",
            "model_name": "gpt-5-mini",
            "feature_name": "ai_reply_generation",
            "prompt_tokens": 120,
            "completion_tokens": 80,
            "estimated_cost": "0.75",
        },
    )
    client.post(
        "/api/v1/posts",
        headers=headers,
        json={
            "title": "Observability launch",
            "content": "Launching reporting foundation now.",
            "generated_by": "human_admin",
            "is_llm_generated": False,
            "requires_approval": False,
            "media_urls": [],
            "metadata_json": {},
        },
    )
    return headers


def test_reporting_and_observability_endpoints(client):
    headers = create_reporting_session(client)

    dashboard_response = client.get("/api/v1/reports/dashboard-summary", headers=headers)
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["current_token_balance"] == 0

    token_usage_response = client.get("/api/v1/reports/token-usage-summary", headers=headers)
    assert token_usage_response.status_code == 200
    assert token_usage_response.json()["total_tokens_consumed"] >= 300

    billing_response = client.get("/api/v1/reports/billing-summary", headers=headers)
    assert billing_response.status_code == 200
    assert billing_response.json()["billed_tokens"] >= 200

    audit_response = client.get("/api/v1/observability/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    assert audit_response.json()["total"] >= 1
