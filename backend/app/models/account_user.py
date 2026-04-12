from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AccountUser(TimestampMixin, Base):
    __tablename__ = "account_users"
    __table_args__ = (UniqueConstraint("account_id", "user_id", name="uq_account_users_account_id_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True, index=True)
    invited_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    account = relationship("Account", back_populates="account_users")
    user = relationship("User", back_populates="account_users")
    role = relationship("Role", back_populates="account_users")
