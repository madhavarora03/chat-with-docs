import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.config import get_settings

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(
    subject: str,
    expire_minutes: Optional[int] = None,
    additional_claims: Optional[dict[str, Any]] = None,
) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(
        minutes=expire_minutes
        if expire_minutes is not None
        else settings.JWT_ACCESS_EXPIRES_MINUTES
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "typ": "access",
    }

    if settings.JWT_ISSUER:
        payload["iss"] = settings.JWT_ISSUER

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload=payload,
        key=settings.JWT_ACCESS_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    options = {"require": ["exp", "sub"]}
    decode_kwargs: dict[str, Any] = {
        "token": token,
        "key": settings.JWT_ACCESS_SECRET,
        "algorithms": [settings.JWT_ALGORITHM],
        "options": options,
    }

    if settings.JWT_ISSUER:
        decode_kwargs["issuer"] = settings.JWT_ISSUER
        options["require"].append("iss")

    try:
        payload = jwt.decode(**decode_kwargs)
        if payload.get("typ") != "access":
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload

    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def create_refresh_token() -> str:
    return secrets.token_urlsafe(settings.REFRESH_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_refresh_token(token: str, token_hash: str) -> bool:
    return secrets.compare_digest(hash_refresh_token(token), token_hash)


def refresh_token_expires_at(
    issued_at: Optional[datetime] = None,
    expires_days: Optional[int] = None,
) -> datetime:
    base_time = issued_at if issued_at is not None else datetime.now(timezone.utc)
    return base_time + timedelta(
        days=expires_days
        if expires_days is not None
        else settings.REFRESH_TOKEN_EXPIRES_DAYS
    )
