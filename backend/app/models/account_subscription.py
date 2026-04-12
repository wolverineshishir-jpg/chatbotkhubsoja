from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import SubscriptionStatus


class AccountSubscription(TimestampMixin, Base):
    __tablename__ = "account_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    billing_plan_id: Mapped[int] = mapped_column(ForeignKey("billing_plans.id"), nullable=False, index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.TRIALING, nullable=False, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    renews_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="subscriptions")
    billing_plan = relationship("BillingPlan", back_populates="subscriptions")
    feature_snapshots = relationship(
        "AccountSubscriptionFeatureSnapshot",
        back_populates="account_subscription",
        cascade="all, delete-orphan",
    )
    token_ledger_entries = relationship("TokenLedger", back_populates="account_subscription")
    billing_transactions = relationship("BillingTransaction", back_populates="account_subscription")
