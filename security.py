"""JWT security — equivalent of plugins/Security.kt.

Generates and validates HS256 tokens with the same audience/issuer/claims as
the Ktor version, and exposes a FastAPI dependency that protects routes the
way `authenticate("auth-jwt")` did.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# These should come from environment variables in a real app (kept identical to
# the Kotlin defaults so existing tokens/clients stay compatible).
JWT_AUDIENCE = "teahouse-api"
JWT_ISSUER = "https://teahouse-api.railway.app/"
JWT_REALM = "teahouse-api"
JWT_SECRET = os.getenv("JWT_SECRET", "secret-key-change-this")
JWT_ALGORITHM = "HS256"

_bearer = HTTPBearer(auto_error=False)


def generate_token(member_id: str) -> str:
    """Create a 1-hour HS256 token carrying the member id claim."""
    now = datetime.now(timezone.utc)
    payload = {
        "aud": JWT_AUDIENCE,
        "iss": JWT_ISSUER,
        "id": member_id,
        "exp": now + timedelta(hours=1),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def require_jwt(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Validate the bearer token; mirrors the Ktor verifier + challenge."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not valid or has expired",
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not valid or has expired",
        )
    return payload
