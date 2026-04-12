from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.schemas.common import ErrorResponse

logger = get_logger(__name__)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    payload = ErrorResponse(
        error="http_error",
        message=str(exc.detail),
        detail=str(exc.detail),
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    payload = ErrorResponse(
        error="validation_error",
        message="Request validation failed.",
        detail="Request validation failed.",
        request_id=_request_id(request),
        details=[
            {
                "loc": list(item["loc"]),
                "msg": item["msg"],
                "type": item["type"],
            }
            for item in exc.errors()
        ],
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.model_dump())


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application exception: %s", exc)
    payload = ErrorResponse(
        error="internal_server_error",
        message="An unexpected error occurred.",
        detail="An unexpected error occurred.",
        request_id=_request_id(request),
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump())
