import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class AgentSessionCreate(BaseModel):
    session_type: str = Field(default="free_chat", max_length=30)
    context_ref: dict | None = None


class AgentSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    session_type: str
    context_ref: dict | None
    status: str
    summary: str | None
    created_at: datetime
    closed_at: datetime | None

    class Config:
        from_attributes = True


class AgentSessionDetail(AgentSessionResponse):
    messages: list["AgentMessageResponse"] = []


class AgentMessageCreate(BaseModel):
    content: str
    content_type: str = "text"


class AgentMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content_type: str
    content: str | None
    audio_url: str | None
    tool_name: str | None
    tool_params: dict | None
    tokens_used: int | None
    latency_ms: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentStreamChunk(BaseModel):
    type: str
    message_id: uuid.UUID | None = None
    payload: dict = {}
    timestamp: str = ""
