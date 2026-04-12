from sqlalchemy import Boolean, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TokenPurchasePackage(TimestampMixin, Base):
    __tablename__ = "token_purchase_packages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    token_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    billing_transactions = relationship("BillingTransaction", back_populates="token_purchase_package")
