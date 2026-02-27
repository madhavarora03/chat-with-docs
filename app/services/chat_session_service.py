from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.core.database import SessionDep
from app.enums import SessionStatus
from app.models import ChatSession
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChatSessionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, user_id: UUID, title: str) -> ChatSession:
        chat_session = ChatSession(user_id=user_id, title=title)
        self.session.add(chat_session)
        self.session.commit()
        self.session.refresh(chat_session)
        logger.info("Created session_id=%s for user_id=%s", chat_session.id, user_id)
        return chat_session

    def list_by_user(
        self, user_id: UUID, status: SessionStatus | None = None
    ) -> list[ChatSession]:
        stmt = select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.status != SessionStatus.DELETED,
        )
        if status is not None:
            stmt = stmt.where(ChatSession.status == status)
        return self.session.exec(stmt).all()

    def get_by_id(self, session_id: UUID, user_id: UUID) -> ChatSession | None:
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        return self.session.exec(stmt).first()

    def update(
        self,
        session_id: UUID,
        user_id: UUID,
        title: str | None = None,
        status: SessionStatus | None = None,
    ) -> ChatSession | None:
        chat_session = self.get_by_id(session_id, user_id)
        if not chat_session:
            return None

        if title is not None:
            chat_session.title = title

        if status is not None:
            chat_session.status = status

        chat_session.updated_at = datetime.now(timezone.utc)
        self.session.add(chat_session)
        self.session.commit()
        self.session.refresh(chat_session)
        logger.info("Updated session_id=%s for user_id=%s", session_id, user_id)
        return chat_session

    def delete(self, session_id: UUID, user_id: UUID) -> bool:
        chat_session = self.get_by_id(session_id, user_id)
        if not chat_session:
            return False

        chat_session.status = SessionStatus.DELETED
        chat_session.updated_at = datetime.now(timezone.utc)
        self.session.add(chat_session)
        self.session.commit()
        logger.info("Soft-deleted session_id=%s for user_id=%s", session_id, user_id)
        return True


def get_chat_session_service(session: SessionDep) -> ChatSessionService:
    return ChatSessionService(session)
