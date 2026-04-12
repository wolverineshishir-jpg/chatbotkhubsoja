from conftest import TestingSessionLocal

from app.models.account import Account
from app.models.billing_transaction import BillingTransaction
from app.models.enums import TokenAllocationType
from app.models.token_ledger import TokenLedger
from app.services.billing_service import BillingService
from scripts.seed_system_data import (
    ensure_feature_catalog,
    ensure_permissions,
    ensure_plans_and_feature_links,
    ensure_role_permissions,
    ensure_roles,
    ensure_token_packages,
)


def _register_and_create_account(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "billing-owner@example.com",
            "password": "password123",
            "full_name": "Billing Owner",
        },
    )
    token = register_response.json()["access_token"]
    account_response = client.post(
        "/api/v1/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Billing Account", "slug": "billing-account"},
    )
    account = account_response.json()
    headers = {"Authorization": f"Bearer {token}", "X-Account-ID": str(account["id"])}
    return headers, account["id"]


def _seed_billing_foundation():
    with TestingSessionLocal() as db:
        permissions = ensure_permissions(db)
        roles = ensure_roles(db)
        ensure_role_permissions(db, roles=roles, permissions=permissions)
        ensure_feature_catalog(db)
        ensure_plans_and_feature_links(db)
        ensure_token_packages(db)
        db.commit()


def test_billing_plan_feature_subscription_wallet_and_history_endpoints(client):
    _seed_billing_foundation()
    headers, _ = _register_and_create_account(client)

    plans_response = client.get("/api/v1/billing/plans", headers=headers)
    assert plans_response.status_code == 200
    starter = next(item for item in plans_response.json()["items"] if item["code"] == "starter_monthly")
    assert starter["features"]

    features_response = client.get("/api/v1/billing/features", headers=headers)
    assert features_response.status_code == 200
    assert features_response.json()["total"] >= 1

    subscribe_response = client.post(
        "/api/v1/billing/subscription",
        headers=headers,
        json={"billing_plan_code": starter["code"], "status": "active"},
    )
    assert subscribe_response.status_code == 201
    subscription = subscribe_response.json()
    assert subscription["plan"]["code"] == starter["code"]

    wallet_response = client.get("/api/v1/billing/wallet", headers=headers)
    assert wallet_response.status_code == 200
    assert wallet_response.json()["breakdown"]["available_monthly_free_tokens"] == starter["monthly_token_credit"]

    transaction_response = client.get("/api/v1/billing/transactions", headers=headers)
    assert transaction_response.status_code == 200
    assert any(item["transaction_type"] == "subscription" for item in transaction_response.json()["items"])

    ledger_response = client.get("/api/v1/billing/token-ledger", headers=headers)
    assert ledger_response.status_code == 200
    assert any(item["allocation_type"] == "monthly_free" for item in ledger_response.json()["items"])


def test_token_package_purchase_and_priority_debit(client):
    _seed_billing_foundation()
    headers, account_id = _register_and_create_account(client)

    subscribe_response = client.post(
        "/api/v1/billing/subscription",
        headers=headers,
        json={"billing_plan_code": "starter_monthly", "status": "active"},
    )
    assert subscribe_response.status_code == 201

    purchase_response = client.post(
        "/api/v1/billing/token-purchases",
        headers=headers,
        json={"package_code": "tokens_10k"},
    )
    assert purchase_response.status_code == 201

    with TestingSessionLocal() as db:
        account = db.get(Account, account_id)
        assert account is not None
        BillingService(db).debit_tokens(
            account=account,
            amount=16000,
            reference_type="test_case",
            reference_id="priority-debit",
            notes="Priority debit test",
        )
        db.commit()

        credits = db.query(TokenLedger).filter(TokenLedger.account_id == account_id, TokenLedger.remaining_tokens.is_not(None)).all()
        monthly_credit = next(item for item in credits if item.allocation_type == TokenAllocationType.MONTHLY_FREE)
        purchased_credit = next(item for item in credits if item.allocation_type == TokenAllocationType.PURCHASED)
        assert monthly_credit.remaining_tokens == 0
        assert purchased_credit.remaining_tokens == 9000

        transactions = db.query(BillingTransaction).filter(BillingTransaction.account_id == account_id).all()
        assert len(transactions) >= 2
