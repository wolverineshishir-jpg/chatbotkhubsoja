from sqlalchemy import Boolean, Enum, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import BillingInterval


class BillingPlan(TimestampMixin, Base):
    __tablename__ = "billing_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    billing_interval: Mapped[BillingInterval] = mapped_column(Enum(BillingInterval), nullable=False, index=True)
    setup_fee_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    price_usd: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    monthly_token_credit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    subscriptions = relationship("AccountSubscription", back_populates="billing_plan")
    plan_features = relationship("PlanFeature", back_populates="billing_plan", cascade="all, delete-orphan")
