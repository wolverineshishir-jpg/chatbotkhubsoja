from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import SyncJobStatus, SyncJobType
from app.models.sync_job import SyncJob


class SyncJobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self,
        *,
        job_type: SyncJobType,
        scheduled_for: datetime | None = None,
        account_id: int | None = None,
        platform_connection_id: int | None = None,
        dedupe_key: str | None = None,
        payload_json: dict | None = None,
        max_attempts: int = 5,
    ) -> SyncJob:
        if dedupe_key:
            existing = self.db.scalar(select(SyncJob).where(SyncJob.dedupe_key == dedupe_key))
            if existing:
                return existing

        job = SyncJob(
            account_id=account_id,
            platform_connection_id=platform_connection_id,
            job_type=job_type,
            status=SyncJobStatus.PENDING,
            dedupe_key=dedupe_key,
            scheduled_for=scheduled_for or self._utcnow(),
            payload_json=payload_json or {},
            result_json={},
            max_attempts=max_attempts,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_running(self, job: SyncJob, *, task_id: str | None = None) -> SyncJob:
        job.status = SyncJobStatus.RUNNING
        job.started_at = self._utcnow()
        job.attempts += 1
        job.last_task_id = task_id
        job.error_message = None
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_completed(self, job: SyncJob, *, result_json: dict | None = None) -> SyncJob:
        job.status = SyncJobStatus.COMPLETED
        job.completed_at = self._utcnow()
        job.retry_after = None
        job.error_message = None
        job.result_json = result_json or {}
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_failed(self, job: SyncJob, *, error_message: str, retry_delay_seconds: int = 120) -> SyncJob:
        exhausted = job.attempts >= job.max_attempts
        job.status = SyncJobStatus.FAILED if exhausted else SyncJobStatus.RETRY_SCHEDULED
        job.error_message = error_message[:500]
        job.retry_after = None if exhausted else self._utcnow() + timedelta(seconds=retry_delay_seconds)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_due_jobs(self, *, limit: int = 100) -> list[SyncJob]:
        now = self._utcnow()
        return self.db.scalars(
            select(SyncJob)
            .where(
                SyncJob.status.in_([SyncJobStatus.PENDING, SyncJobStatus.RETRY_SCHEDULED]),
                SyncJob.scheduled_for <= now,
            )
            .where((SyncJob.retry_after.is_(None)) | (SyncJob.retry_after <= now))
            .order_by(SyncJob.scheduled_for.asc(), SyncJob.id.asc())
            .limit(limit)
        ).all()

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
