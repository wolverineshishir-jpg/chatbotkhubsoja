import logging
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from celery import Task
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

logger = logging.getLogger("app.workers")

P = ParamSpec("P")
R = TypeVar("R")


class LoggedTask(Task):
    autoretry_for = (ConnectionError, TimeoutError)
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True
    max_retries = 5

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        logger.info("Starting task %s [%s] args=%s kwargs=%s", self.name, task_id, args, kwargs)

    def on_success(self, retval, task_id: str, args: tuple, kwargs: dict) -> None:
        logger.info("Completed task %s [%s]", self.name, task_id)

    def on_retry(self, exc: BaseException, task_id: str, args: tuple, kwargs: dict, einfo) -> None:
        logger.warning("Retrying task %s [%s]: %s", self.name, task_id, exc)

    def on_failure(self, exc: BaseException, task_id: str, args: tuple, kwargs: dict, einfo) -> None:
        logger.exception("Failed task %s [%s]: %s", self.name, task_id, exc)


def with_db_session(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        db: Session = SessionLocal()
        try:
            return func(*args, db=db, **kwargs)
        finally:
            db.close()

    return wrapper
