from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = get_settings()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "type": "access", "jti": uuid4().hex, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm=ALGORITHM), expires_at


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    token_jti = uuid4().hex
    payload = {"sub": subject, "type": "refresh", "jti": token_jti, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm=ALGORITHM), token_jti, expires_at


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token.") from exc
