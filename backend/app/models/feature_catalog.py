from sqlalchemy import Boolean, Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import FeatureValueType


class FeatureCatalog(TimestampMixin, Base):
    __tablename__ = "feature_catalog"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    value_type: Mapped[FeatureValueType] = mapped_column(Enum(FeatureValueType), nullable=False, index=True)
    unit_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    plan_features = relationship("PlanFeature", back_populates="feature", cascade="all, delete-orphan")
    subscription_feature_snapshots = relationship(
        "AccountSubscriptionFeatureSnapshot",
        back_populates="feature",
        cascade="all, delete-orphan",
    )
