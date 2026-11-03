
import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash


# Password hashing using Argon2
password_hash = PasswordHash.recommended()

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing. "
        "Add it to your project-root .env file."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    """Securely hash a user's password."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check a password against its stored hash."""
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(user_id: int) -> str:
    """Create a signed JWT for an authenticated user."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    """Verify a JWT and return its user ID."""
    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    user_id = int(payload["sub"])

    if user_id <= 0:
        raise ValueError("Invalid user ID")

    return user_id
