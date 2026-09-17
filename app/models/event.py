from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

class EventCreate(BaseModel):
    organizer_id: UUID
    event_name: str
    description: Optional[str] = None

class EventUpdate(BaseModel):
    event_name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[timedelta] = None
    final_time: Optional[datetime] = None
    final_location: Optional[str] = None
    final_activity: Optional[str] = None
    status: Optional[str] = None

class EventOut(BaseModel):
    event_id: UUID
    organizer_id: UUID
    event_name: str
    description: Optional[str]
    duration: Optional[timedelta]
    final_time: Optional[datetime]
    final_location: Optional[str]
    final_activity: Optional[str]
    status: str
    created_at: datetime