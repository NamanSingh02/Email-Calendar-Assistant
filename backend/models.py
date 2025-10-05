from typing import Optional, List
from sqlmodel import SQLModel, Field
from datetime import datetime

class Message(SQLModel, table=True):
    id: str = Field(primary_key=True)
    thread_id: Optional[str] = None
    subject: Optional[str] = None
    from_email: Optional[str] = None
    sent_at: Optional[datetime] = None
    body_text: Optional[str] = None

class ThreadDigest(SQLModel, table=True):
    thread_id: str = Field(primary_key=True)
    summary: str
    updated_at: datetime

class Task(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    assignee: str  # 'me' | 'them'
    due_iso: Optional[str] = None
    confidence: float = 0.0
    source_thread: Optional[str] = None

class Evidence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str
    email_id: str
    start: int
    end: int
