from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get("", response_model=HealthResponse, summary="Service health check")
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    return HealthService(db).get_status()
