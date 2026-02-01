from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel

from app.enums import Role

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession


class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chatsession.id")
    role: Role
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    session: Optional[ChatSession] = Relationship(back_populates="messages")
