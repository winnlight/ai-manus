from typing import Dict, Optional, List
from datetime import datetime, timezone
from beanie import Document
from app.domain.models.memory import Memory
from app.domain.events.agent_events import AgentEvent
from app.domain.models.session import SessionStatus

class AgentDocument(Document):
    """MongoDB document for Agent"""
    agent_id: str
    model_name: str
    temperature: float
    max_tokens: int
    memories: Dict[str, Memory] = {}
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "agents"
        indexes = [
            "agent_id",
        ]


class SessionDocument(Document):
    """MongoDB model for Session"""
    session_id: str
    sandbox_id: Optional[str] = None
    agent_id: str
    task_id: Optional[str] = None
    title: Optional[str] = None
    unread_message_count: int = 0
    latest_message: Optional[str] = None
    latest_message_at: Optional[datetime] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    events: List[AgentEvent]
    status: SessionStatus

    class Settings:
        name = "sessions"
        indexes = [
            "session_id",
        ]

class AttachmentDocument(Document):
    """model for Attachment"""
    attachment_id: str
    session_id: str
    filename: str
    content_type: str
    file_size: int
    storage_type:str
    storage_url: str
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "attachments"
        indexes = [
            "attachment_id",
            "task_id"
        ]