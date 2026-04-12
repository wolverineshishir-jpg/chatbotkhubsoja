from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import AutomationActionType, AutomationTriggerType, AutomationWorkflowStatus


class AutomationWorkflow(TimestampMixin, Base):
    __tablename__ = "automation_workflows"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    platform_connection_id: Mapped[int | None] = mapped_column(ForeignKey("platform_connections.id"), nullable=True, index=True)
    ai_agent_id: Mapped[int | None] = mapped_column(ForeignKey("ai_agents.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[AutomationWorkflowStatus] = mapped_column(
        Enum(AutomationWorkflowStatus),
        default=AutomationWorkflowStatus.DRAFT,
        nullable=False,
        index=True,
    )
    trigger_type: Mapped[AutomationTriggerType] = mapped_column(Enum(AutomationTriggerType), nullable=False, index=True)
    action_type: Mapped[AutomationActionType] = mapped_column(Enum(AutomationActionType), nullable=False, index=True)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    trigger_filters_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    action_config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    schedule_timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    schedule_local_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_result_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    account = relationship("Account", back_populates="automation_workflows")
    platform_connection = relationship("PlatformConnection", back_populates="automation_workflows")
    ai_agent = relationship("AIAgent", back_populates="automation_workflows")
