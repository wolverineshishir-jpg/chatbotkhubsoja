from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import BillingTransactionStatus, BillingTransactionType


class BillingTransaction(TimestampMixin, Base):
    __tablename__ = "billing_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    account_subscription_id: Mapped[int | None] = mapped_column(ForeignKey("account_subscriptions.id"), nullable=True, index=True)
    token_purchase_package_id: Mapped[int | None] = mapped_column(ForeignKey("token_purchase_packages.id"), nullable=True, index=True)
    transaction_type: Mapped[BillingTransactionType] = mapped_column(Enum(BillingTransactionType), nullable=False, index=True)
    status: Mapped[BillingTransactionStatus] = mapped_column(
        Enum(BillingTransactionStatus),
        default=BillingTransactionStatus.PENDING,
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    tax_usd: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_amount_usd: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="billing_transactions")
    account_subscription = relationship("AccountSubscription", back_populates="billing_transactions")
    token_purchase_package = relationship("TokenPurchasePackage", back_populates="billing_transactions")
    token_ledger_entries = relationship("TokenLedger", back_populates="billing_transaction")
