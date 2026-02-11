from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class TicketStatus(str, Enum):
    OPEN = "open"
    AI_PROCESSING = "ai_processing"
    HUMAN_NEEDED = "human_needed"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Role(str, Enum):
    USER = "user"
    AI = "ai"
    ADMIN = "admin"

class Message(BaseModel):
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    image_url: Optional[str] = None

class Ticket(BaseModel):
    id: str
    user_id: str
    category: str
    title: str
    description: str
    status: TicketStatus = TicketStatus.AI_PROCESSING
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class TicketCreate(BaseModel):
    user_id: str
    category: str
    title: str
    description: str
    image_url: Optional[str] = None
