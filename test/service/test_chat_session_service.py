from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.enums import SessionStatus
from app.exceptions import SessionNotFoundError
from app.models import ChatSession
from app.services.auth_service import AuthService
from app.services.chat_session_service import ChatSessionService


@pytest.fixture(name="chat_session_service")
def chat_session_service_fixture(session: Session) -> ChatSessionService:
    return ChatSessionService(session)


@pytest.fixture(name="auth_service")
def auth_service_fixture(session: Session) -> AuthService:
    return AuthService(session)


@pytest.fixture(name="test_user_id")
def test_user_fixture(auth_service: AuthService) -> UUID:
    return auth_service.create_user(
        email="test@example.com", name="Test User", password="securepassword123"
    ).id


@pytest.fixture(name="other_user_id")
def other_user_fixture(auth_service: AuthService) -> UUID:
    return auth_service.create_user(
        email="other@example.com", name="Other User", password="securepassword123"
    ).id


@pytest.fixture(name="test_session")
def test_session_fixture(
    chat_session_service: ChatSessionService, test_user_id: UUID
) -> ChatSession:
    return chat_session_service.create(test_user_id, "Test Session")


# ─── create ───
def test_create(chat_session_service: ChatSessionService, test_user_id: UUID) -> None:
    session = chat_session_service.create(test_user_id, "New Chat Session")
    assert session.id is not None
    assert session.user_id == test_user_id
    assert session.title == "New Chat Session"
    assert session.status == SessionStatus.ACTIVE


def test_create_nonexistent_user(chat_session_service: ChatSessionService) -> None:
    with pytest.raises(IntegrityError):
        chat_session_service.create(uuid4(), "New Chat Session")


# ─── list_by_user ───
def test_list_by_user_empty(
    chat_session_service: ChatSessionService, test_user_id: UUID
) -> None:
    assert chat_session_service.list_by_user(test_user_id) == []


def test_list_by_user_returns_own_sessions_only(
    chat_session_service: ChatSessionService, test_user_id: UUID, other_user_id: UUID
) -> None:
    chat_session_service.create(test_user_id, "Test User Session")
    chat_session_service.create(other_user_id, "Other User Session")

    assert len(chat_session_service.list_by_user(test_user_id)) == 1
    assert len(chat_session_service.list_by_user(other_user_id)) == 1


def test_list_by_user_excludes_deleted(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    chat_session_service.delete(test_session.id, test_user_id)

    assert chat_session_service.list_by_user(test_user_id) == []


def test_list_by_user_filter_by_status(
    chat_session_service: ChatSessionService, test_user_id: UUID
) -> None:
    chat_session_service.create(test_user_id, "Active Session")

    archived = chat_session_service.create(test_user_id, "Archived Session")
    chat_session_service.update(
        archived.id, test_user_id, status=SessionStatus.ARCHIVED
    )

    results = chat_session_service.list_by_user(
        test_user_id, status=SessionStatus.ARCHIVED
    )
    assert len(results) == 1
    assert results[0].id == archived.id


# ─── find_by_id ───
def test_find_by_id_found(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    result = chat_session_service.find_by_id(test_session.id, test_user_id)
    assert result is not None
    assert result.id == test_session.id


def test_find_by_id_not_found(
    chat_session_service: ChatSessionService, test_user_id: UUID
) -> None:
    assert chat_session_service.find_by_id(uuid4(), test_user_id) is None


def test_find_by_id_wrong_user(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    other_user_id: UUID,
) -> None:
    assert chat_session_service.find_by_id(test_session.id, other_user_id) is None


# ─── get_by_id ───
def test_get_by_id_found(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    result = chat_session_service.get_by_id(test_session.id, test_user_id)
    assert result.id == test_session.id


def test_get_by_id_not_found(
    chat_session_service: ChatSessionService, test_user_id: UUID
) -> None:
    with pytest.raises(SessionNotFoundError):
        chat_session_service.get_by_id(uuid4(), test_user_id)


def test_get_by_id_wrong_user(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    other_user_id: UUID,
) -> None:
    with pytest.raises(SessionNotFoundError):
        chat_session_service.get_by_id(test_session.id, other_user_id)


# ─── update ───
def test_update_title(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    result = chat_session_service.update(
        test_session.id, test_user_id, title="New Title"
    )

    assert result.title == "New Title"
    assert result.status == SessionStatus.ACTIVE


def test_update_status(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    result = chat_session_service.update(
        test_session.id, test_user_id, status=SessionStatus.ARCHIVED
    )

    assert result.status == SessionStatus.ARCHIVED
    assert result.title == "Test Session"


def test_update_both(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    result = chat_session_service.update(
        test_session.id, test_user_id, title="New Title", status=SessionStatus.ARCHIVED
    )

    assert result.title == "New Title"
    assert result.status == SessionStatus.ARCHIVED


def test_update_none_fields_are_noop(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    result = chat_session_service.update(test_session.id, test_user_id)

    assert result.title == "Test Session"
    assert result.status == SessionStatus.ACTIVE


def test_update_nonexistent_session(
    chat_session_service: ChatSessionService, test_user_id: UUID
) -> None:
    result = chat_session_service.update(uuid4(), test_user_id)

    assert result is None


def test_update_wrong_user(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    other_user_id: UUID,
) -> None:
    result = chat_session_service.update(test_session.id, other_user_id)

    assert result is None


# ─── delete ───
def test_delete_success(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    assert chat_session_service.delete(test_session.id, test_user_id) is True
    assert (
        chat_session_service.find_by_id(test_session.id, test_user_id).status
        == SessionStatus.DELETED
    )


def test_delete_nonexistent(
    chat_session_service: ChatSessionService, test_user_id: UUID
) -> None:
    assert chat_session_service.delete(uuid4(), test_user_id) is False


def test_delete_wrong_user(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    other_user_id: UUID,
) -> None:
    assert chat_session_service.delete(test_session.id, other_user_id) is False


def test_delete_removes_from_default_list(
    chat_session_service: ChatSessionService,
    test_session: ChatSession,
    test_user_id: UUID,
) -> None:
    chat_session_service.delete(test_session.id, test_user_id)
    assert chat_session_service.list_by_user(test_user_id) == []
