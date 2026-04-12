from sqlalchemy import Enum, ForeignKey, Integer, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import TokenWalletStatus


class TokenWallet(TimestampMixin, Base):
    __tablename__ = "token_wallets"
    __table_args__ = (UniqueConstraint("account_id", name="uq_token_wallets_account_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    status: Mapped[TokenWalletStatus] = mapped_column(Enum(TokenWalletStatus), default=TokenWalletStatus.ACTIVE, nullable=False, index=True)
    balance_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_credited_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_debited_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="token_wallets")
    ledger_entries = relationship("TokenLedger", back_populates="wallet", cascade="all, delete-orphan")
