from app.schemas.common import APIModel


class HealthResponse(APIModel):
    status: str
    database: str
    version: str
