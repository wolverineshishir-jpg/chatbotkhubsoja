from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permissions
from app.db.session import get_db
from app.models.account import Account
from app.models.enums import AuditActionType, AuditResourceType
from app.models.membership import Membership
from app.models.user import User
from app.schemas.billing import (
    AccountSubscriptionResponse,
    BillingPlanListResponse,
    BillingTransactionListResponse,
    BillingTransactionResponse,
    FeatureCatalogListResponse,
    ManualTokenAdjustmentRequest,
    SubscriptionCreateRequest,
    TokenLedgerListResponse,
    TokenLedgerResponse,
    TokenPackageCreateRequest,
    TokenPackageListResponse,
    TokenPackagePurchaseRequest,
    TokenPackageResponse,
    WalletBalanceResponse,
)
from app.schemas.common import MessageResponse
from app.services.audit_log_service import AuditContext, AuditLogService
from app.services.billing_service import BillingService

router = APIRouter()


@router.get("/plans", response_model=BillingPlanListResponse)
def list_billing_plans(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
) -> BillingPlanListResponse:
    del context
    service = BillingService(db)
    service.seed_default_plans()
    return service.list_plans()


@router.get("/features", response_model=FeatureCatalogListResponse)
def list_billing_features(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
) -> FeatureCatalogListResponse:
    del context
    return BillingService(db).list_features()


@router.get("/subscription", response_model=AccountSubscriptionResponse | None)
def get_account_subscription(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
) -> AccountSubscriptionResponse | None:
    account, _ = context
    return BillingService(db).get_subscription(account=account)


@router.post("/subscription", response_model=AccountSubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_account_subscription(
    request: Request,
    payload: SubscriptionCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("account:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AccountSubscriptionResponse:
    account, _ = context
    response = BillingService(db).create_subscription(account=account, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.ADMIN_ACTION,
        resource_type=AuditResourceType.ACCOUNT,
        resource_id=str(account.id),
        description=f"Created account subscription for {response.plan.code}.",
        metadata_json={"subscription_id": response.id, "status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.put("/subscription", response_model=AccountSubscriptionResponse)
def upsert_account_subscription(
    request: Request,
    payload: SubscriptionCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("account:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AccountSubscriptionResponse:
    account, _ = context
    response = BillingService(db).create_subscription(account=account, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.ADMIN_ACTION,
        resource_type=AuditResourceType.ACCOUNT,
        resource_id=str(account.id),
        description=f"Updated account subscription to {response.plan.code}.",
        metadata_json={"subscription_id": response.id, "status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.get("/wallet", response_model=WalletBalanceResponse)
def get_wallet_balance(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
) -> WalletBalanceResponse:
    account, _ = context
    return BillingService(db).get_wallet_balance(account=account)


@router.get("/transactions", response_model=BillingTransactionListResponse)
def list_billing_transactions(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
) -> BillingTransactionListResponse:
    account, _ = context
    return BillingService(db).list_transactions(account=account)


@router.get("/token-ledger", response_model=TokenLedgerListResponse)
def list_token_ledger_entries(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
) -> TokenLedgerListResponse:
    account, _ = context
    return BillingService(db).list_token_ledger(account=account)


@router.get("/token-packages", response_model=TokenPackageListResponse)
def list_token_packages(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("reports:read"))],
    db: Session = Depends(get_db),
) -> TokenPackageListResponse:
    del context
    return BillingService(db).list_token_packages()


@router.post("/token-packages", response_model=TokenPackageResponse, status_code=status.HTTP_201_CREATED)
def create_token_package(
    request: Request,
    payload: TokenPackageCreateRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("account:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TokenPackageResponse:
    account, _ = context
    response = BillingService(db).create_token_package(payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.ADMIN_ACTION,
        resource_type=AuditResourceType.ACCOUNT,
        resource_id=str(account.id),
        description=f"Created token package {response.code}.",
        metadata_json={"token_package_id": response.id},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/token-purchases", response_model=BillingTransactionResponse, status_code=status.HTTP_201_CREATED)
def purchase_token_package(
    request: Request,
    payload: TokenPackagePurchaseRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("account:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> BillingTransactionResponse:
    account, _ = context
    response = BillingService(db).purchase_token_package(account=account, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.ADMIN_ACTION,
        resource_type=AuditResourceType.ACCOUNT,
        resource_id=str(account.id),
        description=f"Purchased token package for account {account.name}.",
        metadata_json={"billing_transaction_id": response.id, "status": response.status.value},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/token-adjustments", response_model=TokenLedgerResponse, status_code=status.HTTP_201_CREATED)
def manual_token_adjustment(
    request: Request,
    payload: ManualTokenAdjustmentRequest,
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("account:manage"))],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TokenLedgerResponse:
    account, _ = context
    response = BillingService(db).manual_adjust_tokens(account=account, payload=payload)
    AuditLogService(db).record(
        account=account,
        actor=current_user,
        action_type=AuditActionType.ADMIN_ACTION,
        resource_type=AuditResourceType.ACCOUNT,
        resource_id=str(account.id),
        description="Applied manual token adjustment.",
        metadata_json={"token_ledger_id": response.id, "delta_tokens": response.delta_tokens},
        context=AuditContext(ip_address=request.client.host if request.client else None, user_agent=request.headers.get("user-agent")),
    )
    return response


@router.post("/plans/seed", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def seed_billing_plans(
    context: Annotated[tuple[Account, Membership], Depends(require_permissions("account:manage"))],
    db: Session = Depends(get_db),
) -> MessageResponse:
    del context
    created = BillingService(db).seed_default_plans()
    return MessageResponse(message=f"Seeded {created} billing plans.")
