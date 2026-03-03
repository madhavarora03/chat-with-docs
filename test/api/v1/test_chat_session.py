from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.schemas import SignupResponse
from app.services.chat_session_service import ChatSessionService

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
def test_session_fixture(
    auth_client: TestClient, session: Session, test_user: SignupResponse
) -> str:
    user_id = UUID(auth_client.get("/api/v1/auth/me").json()["id"])
    chat_session = ChatSessionService(session).create(user_id, "Test Session")
    return str(chat_session.id)


# ─── list ───
def test_list_sessions_empty(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/chat-sessions")
    assert response.status_code == 200
    assert response.json() == []


def test_list_sessions_returns_own_only(
    client: TestClient, test_user: SignupResponse, session: Session
) -> None:
    user_a_id = UUID(
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user.token.access_token}"},
        ).json()["id"]
    )

    other_resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "other@example.com", "name": "Other", "password": "password123"},
    )
    other_token = other_resp.json()["token"]["access_token"]
    user_b_id = UUID(
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {other_token}"},
        ).json()["id"]
    )

    svc = ChatSessionService(session)
    svc.create(user_a_id, "User A Session")
    svc.create(user_b_id, "User B Session")

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


def test_get_session_wrong_user(
    client: TestClient, test_user: SignupResponse, session: Session
) -> None:
    user_id = UUID(
        client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {test_user.token.access_token}"},
        ).json()["id"]
    )
    chat_session = ChatSessionService(session).create(user_id, "Private")

    other = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "other2@example.com",
            "name": "Other",
            "password": "password123",
        },
    )
    client.headers["Authorization"] = f"Bearer {other.json()['token']['access_token']}"
    response = client.get(f"/api/v1/chat-sessions/{chat_session.id}")
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
