from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession
    from app.models.document_chunk import DocumentChunk


class Document(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_session.id")
    filename: str
    file_path: str
    mime_type: str  # TODO: make enum
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    session: Optional[ChatSession] = Relationship(back_populates="documents")
    chunks: list["DocumentChunk"] = Relationship(back_populates="document")
