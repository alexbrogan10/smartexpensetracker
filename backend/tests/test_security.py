from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import get_settings
from app.core.security import decode_access_token

settings = get_settings()


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def test_decode_rejects_garbage_token():
    assert decode_access_token("not-a-real-token") is None


def test_decode_rejects_token_missing_subject():
    expire = datetime.now(UTC) + timedelta(minutes=30)
    token = _encode({"exp": expire})

    assert decode_access_token(token) is None


def test_decode_rejects_non_uuid_subject():
    expire = datetime.now(UTC) + timedelta(minutes=30)
    token = _encode({"sub": "not-a-uuid", "exp": expire})

    assert decode_access_token(token) is None


def test_decode_rejects_expired_token():
    expired = datetime.now(UTC) - timedelta(minutes=1)
    token = _encode({"sub": "d9b1f5b0-1234-4a2b-8b3e-000000000000", "exp": expired})

    assert decode_access_token(token) is None
