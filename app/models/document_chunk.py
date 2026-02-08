from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    document_id: UUID = Field(foreign_key="documents.id", nullable=False)
    chunk_index: int = Field(..., nullable=False)
    page_start: int = Field(..., nullable=False)
    page_end: int = Field(..., nullable=False)
    content: str = Field(..., nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    document: Optional[Document] = Relationship(back_populates="chunks")
