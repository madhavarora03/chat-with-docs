from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunk(SQLModel, table=True):
    __tablename__ = "document_chunks"
    __table_args__ = (
        sa.Index(
            "ix_document_chunks_document_id_chunk_index", "document_id", "chunk_index"
        ),
    )

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
    document: Document | None = Relationship(back_populates="chunks")
