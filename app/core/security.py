import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Response
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.exceptions import InvalidTokenError
from app.utils.logger import get_logger

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
settings = get_settings()
logger = get_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(
    subject: str,
    expire_minutes: int | None = None,
    additional_claims: dict[str, Any] | None = None,
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
        "jwt": token,
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
            raise InvalidTokenError("Invalid token type")
        return payload

    except jwt.PyJWTError as exc:
        logger.warning("Access token decode failed: %s", exc.__class__.__name__)
        raise InvalidTokenError("Invalid or expired token") from exc


def create_refresh_token() -> str:
    return secrets.token_urlsafe(settings.REFRESH_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_expires_at(
    issued_at: datetime | None = None,
    expires_days: int | None = None,
) -> datetime:
    base_time = issued_at if issued_at is not None else datetime.now(timezone.utc)
    return base_time + timedelta(
        days=expires_days
        if expires_days is not None
        else settings.REFRESH_TOKEN_EXPIRES_DAYS
    )


def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    max_age = settings.REFRESH_TOKEN_EXPIRES_DAYS * 24 * 60 * 60
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.is_dev,
        samesite="lax",
        max_age=max_age,
        path="/api/v1/auth",
    )
