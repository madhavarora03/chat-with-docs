from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.schemas import SignupResponse

SIGNUP_PAYLOAD = {
    "email": "test@example.com",
    "name": "Test User",
    "password": "securepassword123",
}


@pytest.fixture(name="test_user")
def test_user_fixture(client: TestClient) -> SignupResponse:
    response = client.post("/api/v1/auth/signup", json=SIGNUP_PAYLOAD)
    return SignupResponse(**response.json())


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, test_user: SignupResponse) -> TestClient:
    client.headers["Authorization"] = f"Bearer {test_user.token.access_token}"
    return client


@pytest.fixture(name="test_session_id")
def test_session_fixture(auth_client: TestClient) -> str:
    response = auth_client.post("/api/v1/chat-sessions", json={"title": "Test Session"})
    return response.json()["id"]


# ─── create ───
def test_create_session(auth_client: TestClient) -> None:
    response = auth_client.post("/api/v1/chat-sessions", json={"title": "My Session"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Session"
    assert data["status"] == "ACTIVE"
    assert "id" in data
    assert "user_id" in data


def test_create_session_empty_title(auth_client: TestClient) -> None:
    response = auth_client.post("/api/v1/chat-sessions", json={"title": ""})
    assert response.status_code == 422


def test_create_session_unauthenticated(client: TestClient) -> None:
    response = client.post("/api/v1/chat-sessions", json={"title": "My Session"})
    assert response.status_code == 401


# ─── list ───
def test_list_sessions_empty(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/chat-sessions")
    assert response.status_code == 200
    assert response.json() == []


def test_list_sessions_returns_own_only(client: TestClient, test_user) -> None:
    # Create session for test_user
    client.headers["Authorization"] = f"Bearer {test_user.token.access_token}"
    client.post("/api/v1/chat-sessions", json={"title": "User A Session"})

    # Create another user and their session
    other = client.post(
        "/api/v1/auth/signup",
        json={"email": "other@example.com", "name": "Other", "password": "password123"},
    )
    other_token = other.json()["token"]["access_token"]
    client.headers["Authorization"] = f"Bearer {other_token}"
    client.post("/api/v1/chat-sessions", json={"title": "User B Session"})

    # Each user only sees their own
    client.headers["Authorization"] = f"Bearer {test_user.token.access_token}"
    assert len(client.get("/api/v1/chat-sessions").json()) == 1

    client.headers["Authorization"] = f"Bearer {other_token}"
    assert len(client.get("/api/v1/chat-sessions").json()) == 1


def test_list_sessions_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/v1/chat-sessions")
    assert response.status_code == 401


# ─── get ───
def test_get_session(auth_client: TestClient, test_session_id: str) -> None:
    response = auth_client.get(f"/api/v1/chat-sessions/{test_session_id}")
    assert response.status_code == 200
    assert response.json()["id"] == test_session_id


def test_get_session_not_found(auth_client: TestClient) -> None:
    response = auth_client.get(f"/api/v1/chat-sessions/{uuid4()}")
    assert response.status_code == 404


def test_get_session_wrong_user(client: TestClient, test_user) -> None:
    # Create session as test_user
    client.headers["Authorization"] = f"Bearer {test_user.token.access_token}"
    session_id = client.post("/api/v1/chat-sessions", json={"title": "Private"}).json()[
        "id"
    ]

    # Try to access as another user
    other = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "other2@example.com",
            "name": "Other",
            "password": "password123",
        },
    )
    client.headers["Authorization"] = f"Bearer {other.json()['token']['access_token']}"
    response = client.get(f"/api/v1/chat-sessions/{session_id}")
    assert response.status_code == 404


def test_get_session_unauthenticated(client: TestClient, test_session_id: str) -> None:
    client.headers.clear()
    response = client.get(f"/api/v1/chat-sessions/{test_session_id}")
    assert response.status_code == 401


# ─── update ───
def test_update_session_title(auth_client: TestClient, test_session_id: str) -> None:
    response = auth_client.patch(
        f"/api/v1/chat-sessions/{test_session_id}", json={"title": "Updated Title"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_update_session_status(auth_client: TestClient, test_session_id: str) -> None:
    response = auth_client.patch(
        f"/api/v1/chat-sessions/{test_session_id}", json={"status": "ARCHIVED"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ARCHIVED"


def test_update_session_not_found(auth_client: TestClient) -> None:
    response = auth_client.patch(
        f"/api/v1/chat-sessions/{uuid4()}", json={"title": "New"}
    )
    assert response.status_code == 404


def test_update_session_unauthenticated(
    client: TestClient, test_session_id: str
) -> None:
    client.headers.clear()
    response = client.patch(
        f"/api/v1/chat-sessions/{test_session_id}", json={"title": "New"}
    )
    assert response.status_code == 401


# ─── delete ───
def test_delete_session(auth_client: TestClient, test_session_id: str) -> None:
    response = auth_client.delete(f"/api/v1/chat-sessions/{test_session_id}")
    assert response.status_code == 204


def test_delete_session_removes_from_list(
    auth_client: TestClient, test_session_id: str
) -> None:
    auth_client.delete(f"/api/v1/chat-sessions/{test_session_id}")
    assert auth_client.get("/api/v1/chat-sessions").json() == []


def test_delete_session_not_found(auth_client: TestClient) -> None:
    response = auth_client.delete(f"/api/v1/chat-sessions/{uuid4()}")
    assert response.status_code == 404


def test_delete_session_unauthenticated(
    client: TestClient, test_session_id: str
) -> None:
    client.headers.clear()
    response = client.delete(f"/api/v1/chat-sessions/{test_session_id}")
    assert response.status_code == 401
