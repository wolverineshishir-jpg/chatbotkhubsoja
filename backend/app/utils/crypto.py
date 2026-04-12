import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import get_settings


class TokenCipher:
    """
    Placeholder symmetric encryption utility.

    This keeps the storage interface production-oriented while leaving room
    to replace the implementation with KMS or a secrets manager later.
    """

    def __init__(self) -> None:
        settings = get_settings()
        digest = hashlib.sha256(settings.secret_key.get_secret_value().encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))

    def encrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")


token_cipher = TokenCipher()
