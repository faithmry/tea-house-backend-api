import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_AUDIENCE = "teahouse-api"
JWT_ISSUER = "https://teahouse-api.railway.app/"
JWT_REALM = "teahouse-api"
JWT_SECRET = os.getenv("JWT_SECRET", "secret-key-change-this")
JWT_ALGORITHM = "HS256"

_bearer = HTTPBearer(auto_error=False)


def generate_token(member_id: str) -> str:
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
