from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import TokenAllocationType, TokenLedgerEntryType, TokenLedgerSourceType


class TokenLedger(TimestampMixin, Base):
    __tablename__ = "token_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token_wallet_id: Mapped[int] = mapped_column(ForeignKey("token_wallets.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    account_subscription_id: Mapped[int | None] = mapped_column(ForeignKey("account_subscriptions.id"), nullable=True, index=True)
    billing_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("billing_transactions.id"), nullable=True, index=True)
    entry_type: Mapped[TokenLedgerEntryType] = mapped_column(Enum(TokenLedgerEntryType), nullable=False, index=True)
    source_type: Mapped[TokenLedgerSourceType] = mapped_column(Enum(TokenLedgerSourceType), nullable=False, index=True)
    allocation_type: Mapped[TokenAllocationType | None] = mapped_column(Enum(TokenAllocationType), nullable=True, index=True)
    delta_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    unit_price_usd: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    total_price_usd: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    wallet = relationship("TokenWallet", back_populates="ledger_entries")
    account = relationship("Account", back_populates="token_ledger_entries")
    account_subscription = relationship("AccountSubscription", back_populates="token_ledger_entries")
    billing_transaction = relationship("BillingTransaction", back_populates="token_ledger_entries")
