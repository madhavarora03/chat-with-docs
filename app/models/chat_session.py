from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

from app.enums import SessionStatus

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.message import Message
    from app.models.user import User


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_session"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: str
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: SessionStatus = Field(
        sa_column=sa.Column(sa.Enum(SessionStatus, name="session_status")),
        default=SessionStatus.ACTIVE,
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Optional[User] = Relationship(back_populates="sessions")
    document: Optional["Document"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"uselist": False},
    )
    messages: list["Message"] = Relationship(back_populates="session")
