from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import redis

from app.core.config import get_settings

_memory_store: dict[str, tuple[datetime, dict[str, Any]]] = {}


class FacebookOAuthSessionStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._redis_client: redis.Redis | None = None
        try:
            self._redis_client = redis.Redis.from_url(self.settings.celery_broker_url, decode_responses=True)
        except Exception:
            self._redis_client = None

    def create(self, payload: dict[str, Any], *, ttl_seconds: int = 900) -> str:
        session_id = uuid4().hex
        self.save(session_id, payload, ttl_seconds=ttl_seconds)
        return session_id

    def save(self, session_id: str, payload: dict[str, Any], *, ttl_seconds: int = 900) -> None:
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        payload = {**payload, "expires_at": expires_at.isoformat()}
        if self._redis_client is not None:
            try:
                self._redis_client.setex(f"facebook_oauth:{session_id}", ttl_seconds, self._serialize(payload))
                return
            except Exception:
                pass
        _memory_store[session_id] = (expires_at, payload)

    def get(self, session_id: str) -> dict[str, Any] | None:
        if self._redis_client is not None:
            try:
                raw = self._redis_client.get(f"facebook_oauth:{session_id}")
                if raw:
                    return self._deserialize(raw)
            except Exception:
                pass

        item = _memory_store.get(session_id)
        if item is None:
            return None
        expires_at, payload = item
        if expires_at <= datetime.now(UTC):
            _memory_store.pop(session_id, None)
            return None
        return payload

    def delete(self, session_id: str) -> None:
        if self._redis_client is not None:
            try:
                self._redis_client.delete(f"facebook_oauth:{session_id}")
            except Exception:
                pass
        _memory_store.pop(session_id, None)

    @staticmethod
    def _serialize(payload: dict[str, Any]) -> str:
        import json

        return json.dumps(payload)

    @staticmethod
    def _deserialize(payload: str) -> dict[str, Any]:
        import json

        return json.loads(payload)
