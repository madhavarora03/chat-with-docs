from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

from app.enums import SessionStatus

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.message import Message
    from app.models.user import User


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    title: str = Field(..., nullable=False)
    last_active_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    status: SessionStatus = Field(
        sa_column=sa.Column(
            sa.Enum(SessionStatus, name="session_status"), nullable=False
        ),
        default=SessionStatus.ACTIVE,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: User | None = Relationship(back_populates="sessions")
    document: Document | None = Relationship(
        back_populates="session", sa_relationship_kwargs={"uselist": False}
    )
    messages: list["Message"] = Relationship(back_populates="session")
