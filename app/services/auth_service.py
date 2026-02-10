from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlmodel import Session, select
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT

from app.core import security
from app.core.database import SessionDep
from app.models import RefreshToken, User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user:
            # Run hash anyway to prevent timing-based user enumeration
            security.hash_password("dummy")
            logger.warning("Authentication failed: invalid credentials")
            return None
        if not self.verify_password(password, user.password):
            logger.warning("Authentication failed: invalid credentials")
            return None
        return user

    def login(self, email: str, password: str) -> tuple[str, str]:
        """Authenticate user and issue tokens.

        Returns:
            Tuple of (access_token, refresh_token)

        Raises:
            HTTPException: If credentials are invalid.
        """
        user = self.authenticate_user(email, password)
        if not user:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = self.create_access_token(user)
        refresh_token = self.issue_refresh_token(user)
        logger.info("Login successful for user_id=%s", user.id)
        return access_token, refresh_token

    def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.session.exec(stmt).first()

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        return self.session.get(User, user_id)

    def hash_password(self, password: str) -> str:
        return security.hash_password(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return security.verify_password(plain_password, hashed_password)

    def create_access_token(self, user: User) -> str:
        logger.debug("Issuing access token for user_id=%s", user.id)
        return security.create_access_token(subject=str(user.id))

    def issue_refresh_token(self, user: User, *, commit: bool = True) -> str:
        raw_token = security.create_refresh_token()
        token_hash = security.hash_refresh_token(raw_token)
        expires_at = security.refresh_token_expires_at()

        refresh_token = RefreshToken(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )

        self.session.add(refresh_token)
        if commit:
            self.session.commit()

        logger.debug("Issued refresh token for user_id=%s", user.id)
        return raw_token

    def create_user(self, email: str, name: str, password: str) -> User:
        existing_user = self.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=email,
            name=name,
            password=self.hash_password(password),
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """
        Rotate refresh token and issue new access token.

        Returns:
            Tuple of (access_token, new_refresh_token)
        """
        token_hash = security.hash_refresh_token(refresh_token)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > datetime.now(timezone.utc),
            RefreshToken.revoked_at.is_(None),
        )
        stored_token = self.session.exec(stmt).first()

        if not stored_token:
            logger.warning("Refresh token invalid, expired, or revoked")
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = self.get_user_by_id(stored_token.user_id)
        if not user:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Revoke old token and issue new one in a single transaction
        stored_token.revoked_at = datetime.now(timezone.utc)
        self.session.add(stored_token)
        new_refresh_token = self.issue_refresh_token(user, commit=False)
        self.session.commit()

        access_token = self.create_access_token(user)

        logger.debug("Rotated refresh token for user_id=%s", user.id)
        return access_token, new_refresh_token

    def revoke_refresh_token(self, token_id: UUID) -> None:
        token = self.session.get(RefreshToken, token_id)
        if not token or token.revoked_at is not None:
            logger.debug("Refresh token already revoked or missing")
            return
        token.revoked_at = datetime.now(timezone.utc)
        self.session.add(token)
        self.session.commit()
        logger.info("Revoked refresh token token_id=%s", token_id)

    def revoke_all_user_tokens(self, user_id: UUID) -> int:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
        tokens = self.session.exec(stmt).all()
        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked_at = now
            self.session.add(token)
        self.session.commit()
        logger.info("Revoked %d refresh tokens for user_id=%s", len(tokens), user_id)
        return len(tokens)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        return security.decode_access_token(token)

    def get_current_user(self, token: str) -> User:
        payload = self.decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = self.get_user_by_id(user_id)

        if not user:
            logger.warning("User not found for token subject=%s", user_id)
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


def get_current_user(
    token: str = Depends(security.oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    return auth_service.get_current_user(token)
