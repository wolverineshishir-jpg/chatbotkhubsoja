from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request

from app.core.config import Settings
from app.core.logging import get_logger, request_id_context

logger = get_logger("app.request")


class RequestContextMiddleware:
    def __init__(self, app, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        request_id = request.headers.get("x-request-id") or uuid4().hex
        token = request_id_context.set(request_id)
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id
        started_at = time.perf_counter()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                process_time_ms = f"{(time.perf_counter() - started_at) * 1000:.2f}".encode()
                headers.append((b"x-process-time-ms", process_time_ms))
                if not self.settings.rate_limit_enabled:
                    headers.append((b"x-rate-limit-policy", b"not-configured"))
                message["headers"] = headers
            await send(message)

        try:
            logger.info("%s %s", request.method, request.url.path)
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_context.reset(token)
