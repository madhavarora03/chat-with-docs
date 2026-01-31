import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel

from app.models.chat_session import ChatSession


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(..., unique=True)
    name: str
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    sessions: list["ChatSession"] = Relationship(back_populates="user")
