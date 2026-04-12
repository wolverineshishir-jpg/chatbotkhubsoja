from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ORMModel(APIModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class MessageResponse(APIModel):
    message: str


class ErrorResponse(APIModel):
    error: str
    message: str
    detail: str | None = None
    request_id: str | None = None
    details: list[dict] = Field(default_factory=list)
