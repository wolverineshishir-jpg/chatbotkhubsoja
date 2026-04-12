from sqlalchemy import ForeignKey, JSON, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PlanFeature(TimestampMixin, Base):
    __tablename__ = "plan_features"
    __table_args__ = (UniqueConstraint("billing_plan_id", "feature_catalog_id", name="uq_plan_features_plan_feature"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    billing_plan_id: Mapped[int] = mapped_column(ForeignKey("billing_plans.id"), nullable=False, index=True)
    feature_catalog_id: Mapped[int] = mapped_column(ForeignKey("feature_catalog.id"), nullable=False, index=True)
    included_value: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    overage_price_usd: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    billing_plan = relationship("BillingPlan", back_populates="plan_features")
    feature = relationship("FeatureCatalog", back_populates="plan_features")
