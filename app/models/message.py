from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel

from app.models.chat_session import ChatSession
from app.models.enums.role import Role


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chatsession.id")
    role: Role
    name: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    session: Optional[ChatSession] = Relationship(back_populates="messages")
