from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.account_subscription import AccountSubscription
from app.models.billing_plan import BillingPlan
from app.models.billing_transaction import BillingTransaction
from app.models.enums import BillingInterval, BillingTransactionStatus, BillingTransactionType, SubscriptionStatus, TokenLedgerSourceType
from app.models.feature_catalog import FeatureCatalog
from app.models.plan_feature import PlanFeature
from app.models.token_purchase_package import TokenPurchasePackage
from app.schemas.billing import (
    AccountSubscriptionResponse,
    BillingPlanResponse,
    BillingPlanDetailResponse,
    BillingPlanListResponse,
    BillingTransactionListResponse,
    BillingTransactionResponse,
    FeatureCatalogListResponse,
    FeatureCatalogResponse,
    ManualTokenAdjustmentRequest,
    PlanFeatureResponse,
    SubscriptionCreateRequest,
    TokenLedgerListResponse,
    TokenLedgerResponse,
    TokenPackageCreateRequest,
    TokenPackageListResponse,
    TokenPackagePurchaseRequest,
    TokenPackageResponse,
    WalletBalanceResponse,
)
from app.services.subscription_status_service import SubscriptionStatusService
from app.services.token_consumption_service import TokenConsumptionService
from app.services.token_ledger_service import TokenLedgerService
from app.services.token_wallet_service import TokenWalletService


class BillingService:
    def __init__(self, db: Session):
        self.db = db
        self.wallets = TokenWalletService(db)
        self.ledger = TokenLedgerService(db)
        self.consumption = TokenConsumptionService(db)

    def list_plans(self) -> BillingPlanListResponse:
        plans = self.db.scalars(
            select(BillingPlan)
            .where(BillingPlan.is_active.is_(True))
            .options(selectinload(BillingPlan.plan_features).selectinload(PlanFeature.feature))
            .order_by(BillingPlan.price_usd.asc(), BillingPlan.id.asc())
        ).all()
        return BillingPlanListResponse(items=[self._to_plan_response(item) for item in plans], total=len(plans))

    def list_features(self) -> FeatureCatalogListResponse:
        items = self.db.scalars(
            select(FeatureCatalog).where(FeatureCatalog.is_active.is_(True)).order_by(FeatureCatalog.code.asc())
        ).all()
        return FeatureCatalogListResponse(items=[FeatureCatalogResponse.model_validate(item) for item in items], total=len(items))

    def list_token_packages(self) -> TokenPackageListResponse:
        items = self.db.scalars(
            select(TokenPurchasePackage).where(TokenPurchasePackage.is_active.is_(True)).order_by(TokenPurchasePackage.price_usd.asc())
        ).all()
        return TokenPackageListResponse(items=[TokenPackageResponse.model_validate(item) for item in items], total=len(items))

    def create_token_package(self, *, payload: TokenPackageCreateRequest) -> TokenPackageResponse:
        existing = self.db.scalar(select(TokenPurchasePackage).where(TokenPurchasePackage.code == payload.code))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token package code already exists.")
        package = TokenPurchasePackage(**payload.model_dump(), is_active=True)
        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)
        return TokenPackageResponse.model_validate(package)

    def get_subscription(self, *, account: Account) -> AccountSubscriptionResponse | None:
        subscription = self._latest_subscription(account.id)
        if not subscription:
            return None
        return self._to_subscription_response(subscription)

    def create_subscription(self, *, account: Account, payload: SubscriptionCreateRequest) -> AccountSubscriptionResponse:
        plan = self.db.scalar(
            select(BillingPlan)
            .where(BillingPlan.code == payload.billing_plan_code, BillingPlan.is_active.is_(True))
            .options(selectinload(BillingPlan.plan_features).selectinload(PlanFeature.feature))
        )
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing plan not found.")

        now = self._utcnow()
        starts_at = payload.starts_at or now
        renews_at = payload.renews_at or self._default_renews_at(starts_at, plan.billing_interval)
        for row in self._active_subscriptions(account.id):
            row.status = SubscriptionStatus.CANCELED
            row.canceled_at = now
            row.ends_at = row.ends_at or now

        subscription = AccountSubscription(
            account_id=account.id,
            billing_plan_id=plan.id,
            status=payload.status,
            starts_at=starts_at,
            ends_at=payload.ends_at,
            renews_at=renews_at,
            external_subscription_id=payload.external_subscription_id,
            metadata_json=payload.metadata_json,
        )
        self.db.add(subscription)
        self.db.flush()

        transaction = BillingTransaction(
            account_id=account.id,
            account_subscription_id=subscription.id,
            transaction_type=BillingTransactionType.SUBSCRIPTION,
            status=BillingTransactionStatus.SUCCEEDED,
            provider_name="internal",
            currency="USD",
            amount_usd=Decimal(str(plan.price_usd)),
            tax_usd=Decimal("0"),
            total_amount_usd=Decimal(str(plan.setup_fee_usd)) + Decimal(str(plan.price_usd)),
            occurred_at=now,
            paid_at=now,
            metadata_json={"billing_plan_code": plan.code, "setup_fee_usd": str(plan.setup_fee_usd)},
        )
        self.db.add(transaction)
        self.db.flush()

        account.monthly_token_credit = plan.monthly_token_credit
        account.token_credit_next_reset_at = renews_at
        if SubscriptionStatusService.is_active_like(payload.status) and plan.monthly_token_credit > 0:
            self.ledger.credit_monthly_free_tokens(
                account=account,
                amount=plan.monthly_token_credit,
                subscription=subscription,
                metadata_json={"billing_plan_code": plan.code, "reason": "subscription_created"},
            )

        self._refresh_subscription_feature_snapshots(subscription=subscription, plan=plan)
        self.db.commit()
        self.db.refresh(subscription)
        return self._to_subscription_response(subscription)

    def purchase_token_package(self, *, account: Account, payload: TokenPackagePurchaseRequest) -> BillingTransactionResponse:
        package = self.db.scalar(
            select(TokenPurchasePackage).where(
                TokenPurchasePackage.code == payload.package_code,
                TokenPurchasePackage.is_active.is_(True),
            )
        )
        if not package:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token package not found.")
        transaction = BillingTransaction(
            account_id=account.id,
            token_purchase_package_id=package.id,
            transaction_type=BillingTransactionType.TOKEN_PURCHASE,
            status=BillingTransactionStatus.SUCCEEDED,
            provider_name="internal",
            currency=package.currency,
            amount_usd=Decimal(str(package.price_usd)),
            tax_usd=Decimal("0"),
            total_amount_usd=Decimal(str(package.price_usd)),
            occurred_at=self._utcnow(),
            paid_at=self._utcnow(),
            metadata_json=payload.metadata_json,
        )
        self.db.add(transaction)
        self.db.flush()
        self.ledger.credit_token_purchase(
            account=account,
            amount=package.token_amount + package.bonus_tokens,
            billing_transaction=transaction,
            metadata_json={"package_code": package.code},
        )
        self.db.commit()
        self.db.refresh(transaction)
        return BillingTransactionResponse.model_validate(transaction)

    def list_transactions(self, *, account: Account) -> BillingTransactionListResponse:
        items = self.db.scalars(
            select(BillingTransaction)
            .where(BillingTransaction.account_id == account.id)
            .order_by(BillingTransaction.occurred_at.desc(), BillingTransaction.id.desc())
        ).all()
        return BillingTransactionListResponse(items=[BillingTransactionResponse.model_validate(item) for item in items], total=len(items))

    def list_token_ledger(self, *, account: Account) -> TokenLedgerListResponse:
        items = self.ledger.list_entries(account=account)
        return TokenLedgerListResponse(items=[TokenLedgerResponse.model_validate(item) for item in items], total=len(items))

    def get_wallet_balance(self, *, account: Account) -> WalletBalanceResponse:
        return self.wallets.get_wallet_balance(account=account)

    def apply_monthly_credit(self, *, account: Account) -> None:
        subscription = self._latest_subscription(account.id)
        if not subscription or not SubscriptionStatusService.is_active_like(subscription.status):
            return
        if subscription.billing_plan.monthly_token_credit <= 0:
            return
        self.ledger.credit_monthly_free_tokens(
            account=account,
            amount=subscription.billing_plan.monthly_token_credit,
            subscription=subscription,
            metadata_json={"reason": "monthly_reset"},
        )
        account.token_credit_last_applied_at = self._utcnow()
        account.token_credit_next_reset_at = self._default_renews_at(self._utcnow(), subscription.billing_plan.billing_interval)

    def expire_monthly_tokens(self, *, account: Account | None = None) -> int:
        return self.ledger.expire_tokens(account=account)

    def debit_tokens(
        self,
        *,
        account: Account,
        amount: int,
        reference_type: str,
        reference_id: str | None,
        notes: str | None = None,
        metadata_json: dict | None = None,
    ):
        return self.consumption.debit_tokens(
            account=account,
            amount=amount,
            reference_type=reference_type,
            reference_id=reference_id,
            source_type=TokenLedgerSourceType.AI_USAGE,
            notes=notes,
            metadata_json=metadata_json,
        )

    def manual_adjust_tokens(self, *, account: Account, payload: ManualTokenAdjustmentRequest) -> TokenLedgerResponse:
        if payload.delta_tokens < 0:
            entry = self.consumption.debit_tokens(
                account=account,
                amount=abs(payload.delta_tokens),
                reference_type="manual_adjustment",
                reference_id=None,
                source_type=TokenLedgerSourceType.ADMIN,
                notes=payload.notes,
                metadata_json=payload.metadata_json,
            )
        else:
            entry = self.ledger.manual_adjustment(
                account=account,
                delta_tokens=payload.delta_tokens,
                notes=payload.notes,
                metadata_json=payload.metadata_json,
            )
        self.db.commit()
        self.db.refresh(entry)
        return TokenLedgerResponse.model_validate(entry)

    def seed_default_plans(self) -> int:
        defaults = [
            {
                "code": "starter_monthly",
                "name": "Starter Monthly",
                "description": "Starter plan for growing teams launching automation workflows.",
                "billing_interval": BillingInterval.MONTHLY,
                "setup_fee_usd": 0,
                "price_usd": 29,
                "monthly_token_credit": 15000,
            },
            {
                "code": "growth_monthly",
                "name": "Growth Monthly",
                "description": "Growth plan for active teams with higher automation volume.",
                "billing_interval": BillingInterval.MONTHLY,
                "setup_fee_usd": 99,
                "price_usd": 99,
                "monthly_token_credit": 60000,
            },
            {
                "code": "growth_yearly",
                "name": "Growth Yearly",
                "description": "Annual growth plan with discounted pricing.",
                "billing_interval": BillingInterval.YEARLY,
                "setup_fee_usd": 99,
                "price_usd": 990,
                "monthly_token_credit": 60000,
            },
        ]
        created = 0
        feature_map = {feature.code: feature for feature in self.db.scalars(select(FeatureCatalog)).all()}
        feature_links = {
            "starter_monthly": {
                "monthly_tokens": Decimal("15000"),
                "team_members": Decimal("3"),
                "platform_connections": Decimal("2"),
                "ai_agents": Decimal("2"),
                "automation_workflows": Decimal("5"),
                "advanced_reporting": Decimal("0"),
            },
            "growth_monthly": {
                "monthly_tokens": Decimal("60000"),
                "team_members": Decimal("10"),
                "platform_connections": Decimal("10"),
                "ai_agents": Decimal("8"),
                "automation_workflows": Decimal("25"),
                "advanced_reporting": Decimal("1"),
            },
            "growth_yearly": {
                "monthly_tokens": Decimal("60000"),
                "team_members": Decimal("10"),
                "platform_connections": Decimal("10"),
                "ai_agents": Decimal("8"),
                "automation_workflows": Decimal("25"),
                "advanced_reporting": Decimal("1"),
            },
        }
        for payload in defaults:
            existing = self.db.scalar(select(BillingPlan).where(BillingPlan.code == payload["code"]))
            if existing:
                existing.setup_fee_usd = payload["setup_fee_usd"]
                existing.price_usd = payload["price_usd"]
                existing.monthly_token_credit = payload["monthly_token_credit"]
                plan = existing
            else:
                plan = BillingPlan(**payload)
                self.db.add(plan)
                self.db.flush()
                created += 1
            for feature_code, included_value in feature_links.get(plan.code, {}).items():
                feature = feature_map.get(feature_code)
                if feature is None:
                    continue
                link = self.db.scalar(
                    select(PlanFeature).where(
                        PlanFeature.billing_plan_id == plan.id,
                        PlanFeature.feature_catalog_id == feature.id,
                    )
                )
                if link is None:
                    self.db.add(
                        PlanFeature(
                            billing_plan_id=plan.id,
                            feature_catalog_id=feature.id,
                            included_value=included_value,
                            config_json={},
                        )
                    )
                else:
                    link.included_value = included_value
        self.db.commit()
        return created

    def _active_subscriptions(self, account_id: int) -> list[AccountSubscription]:
        return self.db.scalars(
            select(AccountSubscription).where(
                AccountSubscription.account_id == account_id,
                AccountSubscription.status.in_(list(SubscriptionStatusService.ACTIVE_STATUSES)),
            )
        ).all()

    def _latest_subscription(self, account_id: int) -> AccountSubscription | None:
        return self.db.scalar(
            select(AccountSubscription)
            .where(AccountSubscription.account_id == account_id)
            .options(
                selectinload(AccountSubscription.billing_plan).selectinload(BillingPlan.plan_features).selectinload(PlanFeature.feature)
            )
            .order_by(AccountSubscription.created_at.desc(), AccountSubscription.id.desc())
        )

    def _refresh_subscription_feature_snapshots(self, *, subscription: AccountSubscription, plan: BillingPlan) -> None:
        from app.models.account_subscription_feature_snapshot import AccountSubscriptionFeatureSnapshot

        self.db.query(AccountSubscriptionFeatureSnapshot).filter(
            AccountSubscriptionFeatureSnapshot.account_subscription_id == subscription.id
        ).delete()
        for plan_feature in plan.plan_features:
            self.db.add(
                AccountSubscriptionFeatureSnapshot(
                    account_subscription_id=subscription.id,
                    feature_catalog_id=plan_feature.feature_catalog_id,
                    feature_code=plan_feature.feature.code,
                    feature_name=plan_feature.feature.name,
                    included_value=plan_feature.included_value,
                    config_json=plan_feature.config_json or {},
                )
            )

    @staticmethod
    def _default_renews_at(starts_at: datetime, interval: BillingInterval) -> datetime:
        if interval == BillingInterval.YEARLY:
            return starts_at + timedelta(days=365)
        return starts_at + timedelta(days=30)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _to_plan_response(plan: BillingPlan) -> BillingPlanDetailResponse:
        return BillingPlanDetailResponse(
            **BillingPlanResponse.model_validate(plan).model_dump(),
            features=[
                PlanFeatureResponse(
                    feature=FeatureCatalogResponse.model_validate(item.feature),
                    included_value=Decimal(str(item.included_value)),
                    overage_price_usd=Decimal(str(item.overage_price_usd)) if item.overage_price_usd is not None else None,
                    config_json=item.config_json or {},
                )
                for item in plan.plan_features
            ],
        )

    def _to_subscription_response(self, subscription: AccountSubscription) -> AccountSubscriptionResponse:
        plan = subscription.billing_plan
        if plan is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Subscription plan missing.")
        return AccountSubscriptionResponse(
            id=subscription.id,
            account_id=subscription.account_id,
            billing_plan_id=subscription.billing_plan_id,
            status=subscription.status,
            starts_at=subscription.starts_at,
            ends_at=subscription.ends_at,
            renews_at=subscription.renews_at,
            canceled_at=subscription.canceled_at,
            external_subscription_id=subscription.external_subscription_id,
            metadata_json=subscription.metadata_json or {},
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            plan=self._to_plan_response(plan),
        )
