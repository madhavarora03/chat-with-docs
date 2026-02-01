from datetime import datetime, timezone
from mailbox import Message
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel

from app.models.document import Document
from app.models.enums.session_status import SessionStatus
from app.models.user import User


class ChatSession(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: str
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Optional[User] = Relationship(back_populates="sessions")
    documents: list["Document"] = Relationship(back_populates="session")
    messages: list["Message"] = Relationship(back_populates="session")
