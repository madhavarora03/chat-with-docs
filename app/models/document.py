from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession
    from app.models.document_chunk import DocumentChunk


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    session_id: UUID = Field(
        foreign_key="chat_sessions.id", unique=True, nullable=False
    )
    filename: str = Field(..., nullable=False)
    file_path: str = Field(..., nullable=False)
    mime_type: str = Field(..., nullable=False)  # TODO: make enum
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    session: Optional["ChatSession"] = Relationship(back_populates="document")
    chunks: list["DocumentChunk"] = Relationship(back_populates="document")
