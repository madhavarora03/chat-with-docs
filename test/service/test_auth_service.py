import pytest
from sqlmodel import Session

from app.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.models import User
from app.services.auth_service import AuthService


@pytest.fixture(name="auth_service")
def auth_service_fixture(session: Session) -> AuthService:
    return AuthService(session)


@pytest.fixture(name="test_user")
def test_user_fixture(auth_service: AuthService) -> User:
    return auth_service.create_user(
        email="test@example.com", name="Test User", password="securepassword123"
    )


# ─── create_user ───
def test_create_user(auth_service: AuthService):
    user = auth_service.create_user(
        email="new@example.com", name="New User", password="password1234"
    )
    assert user.email == "new@example.com"
    assert user.name == "New User"
    assert user.password != "password1234"


def test_create_user_duplicate_email(auth_service: AuthService, test_user):
    with pytest.raises(DuplicateEmailError):
        auth_service.create_user(
            email="test@example.com", name="Test User", password="securepassword123"
        )


# ─── authenticate_user ───
def test_authenticate_user_success(auth_service: AuthService, test_user):
    user = auth_service.authenticate_user(
        email="test@example.com", password="securepassword123"
    )
    assert user is not None
    assert user.email == "test@example.com"


def test_authenticate_user_wrong_password(auth_service: AuthService, test_user):
    user = auth_service.authenticate_user(
        email="test@example.com", password="wrongpassword"
    )
    assert user is None


def test_authenticate_user_nonexistent(auth_service: AuthService):
    user = auth_service.authenticate_user(
        email="nobody@example.com", password="password1234"
    )
    assert user is None


# ─── login ───
def test_login_success(auth_service: AuthService, test_user):
    access_token, refresh_token = auth_service.login(
        email="test@example.com", password="securepassword123"
    )
    assert access_token
    assert refresh_token


def test_login_invalid_credentials(auth_service: AuthService, test_user):
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(email="test@example.com", password="wrongpassword")


# ─── refresh_tokens ───
def test_refresh_tokens_success(auth_service: AuthService, test_user):
    _, old_refresh = auth_service.login(
        email="test@example.com", password="securepassword123"
    )
    access_token, new_refresh = auth_service.refresh_tokens(old_refresh)
    assert access_token
    assert new_refresh
    assert new_refresh != old_refresh


def test_refresh_tokens_invalid(auth_service: AuthService):
    with pytest.raises(InvalidTokenError):
        auth_service.refresh_tokens("invalid.refresh.token")


def test_refresh_tokens_reuse_revoked(auth_service: AuthService, test_user):
    _, raw_refresh = auth_service.login("test@example.com", "securepassword123")
    auth_service.refresh_tokens(raw_refresh)  # first use — OK
    with pytest.raises(InvalidTokenError):
        auth_service.refresh_tokens(raw_refresh)  # reuse — revoked


# ─── revoke_all_user_tokens ───
def test_revoke_all_user_tokens(auth_service: AuthService, test_user: User):
    auth_service.login(email="test@example.com", password="securepassword123")
    auth_service.login(email="test@example.com", password="securepassword123")
    revoked = auth_service.revoke_all_user_tokens(test_user.id)
    assert revoked >= 1


# ─── get_current_user ───
def test_get_current_user_success(auth_service: AuthService, test_user: User):
    access_token = auth_service.create_access_token(test_user)
    user = auth_service.get_current_user(access_token)
    assert user.id == test_user.id


def test_get_current_user_invalid_token(auth_service: AuthService):
    with pytest.raises(InvalidTokenError):
        auth_service.get_current_user("invalid.token.here")
