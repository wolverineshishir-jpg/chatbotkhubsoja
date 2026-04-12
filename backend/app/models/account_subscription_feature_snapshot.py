from sqlalchemy import ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AccountSubscriptionFeatureSnapshot(TimestampMixin, Base):
    __tablename__ = "account_subscription_feature_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "account_subscription_id",
            "feature_catalog_id",
            name="uq_account_subscription_feature_snapshot_subscription_feature",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_subscription_id: Mapped[int] = mapped_column(ForeignKey("account_subscriptions.id"), nullable=False, index=True)
    feature_catalog_id: Mapped[int] = mapped_column(ForeignKey("feature_catalog.id"), nullable=False, index=True)
    feature_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    feature_name: Mapped[str] = mapped_column(String(255), nullable=False)
    included_value: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account_subscription = relationship("AccountSubscription", back_populates="feature_snapshots")
    feature = relationship("FeatureCatalog", back_populates="subscription_feature_snapshots")
