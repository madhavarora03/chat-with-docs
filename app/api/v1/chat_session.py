from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from app.exceptions import SessionNotFoundError
from app.models import User
from app.schemas.chat_session import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
)
from app.services.auth_service import get_current_user
from app.services.chat_session_service import (
    ChatSessionService,
    get_chat_session_service,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat-sessions", tags=["chat_sessions"])


@router.post("", response_model=ChatSessionResponse, status_code=HTTP_201_CREATED)
def create_session(
    payload: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
) -> ChatSessionResponse:
    session = chat_session_service.create(current_user.id, payload.title)
    logger.info("Created session_id=%s for user_id=%s", session.id, current_user.id)
    return session


@router.get("", response_model=list[ChatSessionResponse])
def list_sessions(
    current_user: User = Depends(get_current_user),
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
) -> list[ChatSessionResponse]:
    return chat_session_service.list_by_user(current_user.id)


@router.get("/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
) -> ChatSessionResponse:
    try:
        return chat_session_service.get_by_id(session_id, current_user.id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.patch("/{session_id}", response_model=ChatSessionResponse)
def update_session(
    session_id: UUID,
    payload: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
) -> ChatSessionResponse:
    try:
        chat_session_service.get_by_id(session_id, current_user.id)
        return chat_session_service.update(
            session_id, current_user.id, title=payload.title, status=payload.status
        )
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.delete("/{session_id}", status_code=HTTP_204_NO_CONTENT)
def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
) -> None:
    try:
        chat_session_service.get_by_id(session_id, current_user.id)
        chat_session_service.delete(session_id, current_user.id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=exc.message) from exc
