from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import SyncJobStatus, SyncJobType


class SyncJob(TimestampMixin, Base):
    __tablename__ = "sync_jobs"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_sync_jobs_dedupe_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(
        ForeignKey("platform_connections.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[SyncJobStatus] = mapped_column(
        Enum(SyncJobStatus),
        default=SyncJobStatus.PENDING,
        nullable=False,
        index=True,
    )
    job_type: Mapped[SyncJobType] = mapped_column(Enum(SyncJobType), nullable=False, index=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    retry_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    last_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="sync_jobs")
    platform_connection = relationship("PlatformConnection", back_populates="sync_jobs")
