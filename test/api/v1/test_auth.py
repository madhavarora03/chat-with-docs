import pytest
from fastapi.testclient import TestClient

from app.schemas import SignupResponse, TokenResponse

SIGNUP_PAYLOAD = {
    "email": "test@example.com",
    "name": "Test User",
    "password": "securepassword123",
}


@pytest.fixture(name="test_user")
def test_user_fixture(client: TestClient) -> SignupResponse:
    """Create a test user via signup and return the response data."""
    response = client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    return SignupResponse(**response.json())


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, test_user: SignupResponse) -> TestClient:
    """Client with Authorization header set from the signup token."""
    client.headers["Authorization"] = f"Bearer {test_user.token.access_token}"
    return client


# ─── Signup ───
def test_signup_success(client: TestClient):
    response = client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["name"] == "Test User"
    assert "access_token" in data["token"]


def test_signup_duplicate_email(client: TestClient, test_user):
    response = client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    assert response.status_code == 409


def test_signup_short_password(client: TestClient):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "x@example.com", "name": "X", "password": "short"},
    )
    assert response.status_code == 422


def test_signup_invalid_email(client: TestClient):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "name": "X", "password": "password1234"},
    )
    assert response.status_code == 422


def test_signup_sets_refresh_cookie(client: TestClient):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "cookie@example.com",
            "name": "Cookie",
            "password": "password1234",
        },
    )
    assert response.status_code == 201
    assert "refresh_token" in response.cookies


# ─── Login ───
def test_login_success(client: TestClient, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.cookies


def test_login_wrong_password(client: TestClient, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password1234"},
    )
    assert response.status_code == 401


# ─── Token (OAuth2 form) ───
def test_token_endpoint(client: TestClient, test_user):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


# ─── Me ───
def test_me_authenticated(auth_client: TestClient):
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


def test_me_no_token(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_invalid_token(client: TestClient):
    client.headers["Authorization"] = "Bearer invalidtoken"
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


# ─── Refresh ───
def test_refresh_success(client: TestClient, test_user):
    # Login to get a refresh cookie
    client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_no_cookie(client: TestClient):
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_refresh_invalid_cookie(client: TestClient):
    client.cookies.set("refresh_token", "bogus_token")
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


# ─── Logout ───
def test_logout_success(auth_client: TestClient):
    response = auth_client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


def test_logout_no_token(client: TestClient):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 401


def test_logout_invalidates_refresh(client: TestClient, test_user):
    # Login to get tokens
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token_response = TokenResponse(**login_resp.json())

    # Logout
    client.headers["Authorization"] = f"Bearer {token_response.access_token}"
    client.post("/api/v1/auth/logout")

    # Refresh should now fail
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
