import uuid
from typing import Optional
from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[uuid.UUID] = None

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 10000:
            raise ValueError("Message too long (max 10000 characters)")
        return v.strip()


class ChatResponse(BaseModel):
    reply: str
    conversation_id: uuid.UUID
    message_id: uuid.UUID