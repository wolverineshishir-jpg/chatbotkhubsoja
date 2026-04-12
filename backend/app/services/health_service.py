from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.health import HealthResponse


class HealthService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def get_status(self) -> HealthResponse:
        database_status = "up"
        try:
            self.db.execute(text("SELECT 1"))
        except Exception:
            database_status = "down"

        return HealthResponse(
            status="ok" if database_status == "up" else "degraded",
            database=database_status,
            version=self.settings.app_version,
        )
