from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.core.config import settings


def _get_fernet() -> Fernet:
    key = settings.SECRET_KEY.encode()
    padded = (key * 32)[:32]
    import base64
    return Fernet(base64.urlsafe_b64encode(padded))


def encrypt_token(token: str) -> bytes:
    return _get_fernet().encrypt(token.encode())


def decrypt_token(encrypted: bytes) -> Optional[str]:
    try:
        return _get_fernet().decrypt(encrypted).decode()
    except (InvalidToken, Exception):
        return None


def create_access_token(user_id: int, github_username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": github_username,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
