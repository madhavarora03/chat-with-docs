from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import SessionStatus


class ChatSessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ChatSessionUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    status: SessionStatus | None = None


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    status: SessionStatus
    last_active_at: datetime
    created_at: datetime
    updated_at: datetime
