import json
from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "SaaS Chat Automation Platform"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    log_level: str = "INFO"
    docs_enabled: bool = True
    secret_key: SecretStr = Field(..., min_length=32)
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    allowed_hosts: list[str] = Field(default_factory=lambda: ["*"])

    mysql_user: str = "app"
    mysql_password: SecretStr = Field(default=SecretStr("app"))
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_database: str = "automation"
    database_url: str | None = None

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str | None = None
    celery_task_always_eager: bool = False
    celery_task_eager_propagates: bool = False
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    facebook_app_id: str | None = None
    facebook_app_secret: SecretStr = Field(default=SecretStr(""))
    facebook_graph_api_version: str = "v23.0"
    facebook_graph_api_base_url: str = "https://graph.facebook.com"
    facebook_oauth_dialog_url: str = "https://www.facebook.com/dialog/oauth"
    facebook_oauth_redirect_uri: str = "http://localhost:5173/connections/facebook/callback"
    facebook_http_timeout_seconds: int = 30
    whatsapp_graph_api_base_url: str = "https://graph.facebook.com"
    whatsapp_graph_api_version: str = "v23.0"
    whatsapp_http_timeout_seconds: int = 30
    whatsapp_verify_signature: bool = True
    openai_api_key: SecretStr = Field(default=SecretStr(""))
    openai_base_url: str | None = None
    openai_organization_id: str | None = None
    openai_project_id: str | None = None
    openai_timeout_seconds: int = 30
    llm_default_provider: str = "internal"
    llm_default_model: str = "internal-reply-model-v1"
    openai_reply_primary_model: str = "gpt-5.4-nano"
    openai_reply_fallback_model: str = "gpt-5.4-mini"
    openai_reply_confidence_threshold: float = 0.55
    ai_token_debit_enabled: bool = True
    owner_email: str = "admin@khubsoja.com"
    owner_password: SecretStr = Field(default=SecretStr("12331233"))
    owner_full_name: str = "System Owner"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password.get_secret_value()}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_broker_url(self) -> str:
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_result_backend(self) -> str:
        return self.celery_broker_url

    def safe_dump(self) -> dict[str, Any]:
        return self.model_dump(
            exclude={
                "secret_key",
                "mysql_password",
                "database_url",
                "redis_url",
                "facebook_app_secret",
                "openai_api_key",
            }
        )

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def parse_list_from_env(cls, value: Any):
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return []
            if normalized.startswith("["):
                try:
                    parsed = json.loads(normalized)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in normalized.split(",") if item.strip()]
        return value

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        value = value.strip().lower()
        allowed = {"development", "test", "staging", "production"}
        if value not in allowed:
            raise ValueError(f"environment must be one of: {', '.join(sorted(allowed))}")
        return value

    @field_validator("cors_origins")
    @classmethod
    def normalize_cors_origins(cls, value: list[str]) -> list[str]:
        return [origin.strip().rstrip("/") for origin in value if origin.strip()]

    @field_validator("allowed_hosts")
    @classmethod
    def normalize_allowed_hosts(cls, value: list[str]) -> list[str]:
        return [host.strip().lower() for host in value if host.strip()]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError(f"log_level must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("openai_reply_confidence_threshold")
    @classmethod
    def validate_openai_reply_confidence_threshold(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("openai_reply_confidence_threshold must be between 0 and 1.")
        return value

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "dev", "development", "true", "1", "yes", "on"}:
                return True
        return value

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.environment == "production":
            if self.debug:
                raise ValueError("debug must be false in production.")
            if self.secret_key.get_secret_value().startswith("change-this"):
                raise ValueError("secret_key must be overridden in production.")
            if "*" in self.allowed_hosts:
                raise ValueError("allowed_hosts cannot include '*' in production.")
            if "*" in self.cors_origins:
                raise ValueError("cors_origins cannot include '*' in production.")
            if self.owner_password.get_secret_value() == "12331233":
                raise ValueError("owner_password must be overridden in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
