from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class Repository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], db: Session):
        self.model = model
        self.db = db

    def get(self, record_id: int) -> ModelT | None:
        return self.db.get(self.model, record_id)

    def list(self) -> Sequence[ModelT]:
        return self.db.scalars(select(self.model)).all()
