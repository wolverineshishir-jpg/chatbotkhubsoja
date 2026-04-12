from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import MembershipRole


class OnboardingKey(TimestampMixin, Base):
    __tablename__ = "onboarding_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    role: Mapped[MembershipRole] = mapped_column(Enum(MembershipRole), default=MembershipRole.ADMIN, nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invited_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    account = relationship("Account", back_populates="onboarding_keys")
