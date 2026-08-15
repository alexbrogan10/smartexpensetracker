from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# bcrypt has a hard 72-byte input limit; UserCreate/PasswordChange schemas
# cap password length at this value so hashing can never raise here.
_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    encoded = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(encoded, hashed_password.encode("utf-8"))


def create_access_token(subject: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> UUID | None:
    """Decode and validate a JWT, returning the user id it was issued for.

    Returns None on any failure (expired, malformed, wrong signature, or a
    subject that isn't a valid UUID) so callers can treat this as a single
    "not authenticated" case.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None

    subject = payload.get("sub")
    if subject is None:
        return None

    try:
        return UUID(subject)
    except ValueError:
        return None
