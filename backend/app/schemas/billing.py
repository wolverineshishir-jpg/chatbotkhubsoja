from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    BillingInterval,
    BillingTransactionStatus,
    BillingTransactionType,
    SubscriptionStatus,
    TokenAllocationType,
    TokenLedgerEntryType,
    TokenLedgerSourceType,
    TokenWalletStatus,
)
from app.schemas.common import ORMModel


class BillingPlanResponse(ORMModel):
    id: int
    code: str
    name: str
    description: str | None
    billing_interval: BillingInterval
    setup_fee_usd: Decimal
    price_usd: Decimal
    monthly_token_credit: int
    is_active: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureCatalogResponse(ORMModel):
    id: int
    code: str
    name: str
    description: str | None
    value_type: str
    unit_label: str | None
    is_active: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PlanFeatureResponse(BaseModel):
    feature: FeatureCatalogResponse
    included_value: Decimal
    overage_price_usd: Decimal | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)


class BillingPlanDetailResponse(BillingPlanResponse):
    features: list[PlanFeatureResponse] = Field(default_factory=list)


class AccountSubscriptionResponse(ORMModel):
    id: int
    account_id: int
    billing_plan_id: int
    status: SubscriptionStatus
    starts_at: datetime
    ends_at: datetime | None
    renews_at: datetime | None
    canceled_at: datetime | None
    external_subscription_id: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    plan: BillingPlanDetailResponse


class TokenWalletResponse(ORMModel):
    id: int
    account_id: int
    status: TokenWalletStatus
    balance_tokens: int
    reserved_tokens: int
    lifetime_credited_tokens: int
    lifetime_debited_tokens: int
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TokenBalanceBreakdown(BaseModel):
    available_monthly_free_tokens: int
    available_purchased_tokens: int
    available_manual_tokens: int
    total_available_tokens: int
    expiring_next_tokens: int


class WalletBalanceResponse(BaseModel):
    wallet: TokenWalletResponse
    breakdown: TokenBalanceBreakdown


class BillingTransactionResponse(ORMModel):
    id: int
    account_id: int
    account_subscription_id: int | None
    token_purchase_package_id: int | None
    transaction_type: BillingTransactionType
    status: BillingTransactionStatus
    provider_name: str | None
    external_reference: str | None
    currency: str
    amount_usd: Decimal
    tax_usd: Decimal
    total_amount_usd: Decimal
    occurred_at: datetime
    paid_at: datetime | None
    failed_at: datetime | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TokenLedgerResponse(ORMModel):
    id: int
    token_wallet_id: int
    account_id: int
    account_subscription_id: int | None
    billing_transaction_id: int | None
    entry_type: TokenLedgerEntryType
    source_type: TokenLedgerSourceType
    allocation_type: TokenAllocationType | None
    delta_tokens: int
    balance_before: int
    balance_after: int
    remaining_tokens: int | None
    expires_at: datetime | None
    expired_at: datetime | None
    is_expired: bool
    unit_price_usd: Decimal | None
    total_price_usd: Decimal | None
    reference_type: str | None
    reference_id: str | None
    notes: str | None
    occurred_at: datetime
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BillingPlanListResponse(BaseModel):
    items: list[BillingPlanDetailResponse]
    total: int


class FeatureCatalogListResponse(BaseModel):
    items: list[FeatureCatalogResponse]
    total: int


class TokenPackageResponse(ORMModel):
    id: int
    code: str
    name: str
    description: str | None
    token_amount: int
    bonus_tokens: int
    price_usd: Decimal
    currency: str
    is_active: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TokenPackageListResponse(BaseModel):
    items: list[TokenPackageResponse]
    total: int


class BillingTransactionListResponse(BaseModel):
    items: list[BillingTransactionResponse]
    total: int


class TokenLedgerListResponse(BaseModel):
    items: list[TokenLedgerResponse]
    total: int


class SubscriptionCreateRequest(BaseModel):
    billing_plan_code: str = Field(..., min_length=2, max_length=64)
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    renews_at: datetime | None = None
    external_subscription_id: str | None = Field(default=None, max_length=255)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class TokenPackageCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    token_amount: int = Field(..., ge=1)
    bonus_tokens: int = Field(default=0, ge=0)
    price_usd: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=8)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class TokenPackagePurchaseRequest(BaseModel):
    package_code: str = Field(..., min_length=2, max_length=100)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ManualTokenAdjustmentRequest(BaseModel):
    delta_tokens: int
    notes: str | None = Field(default=None, max_length=500)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
