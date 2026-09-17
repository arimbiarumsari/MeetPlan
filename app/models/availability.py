from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class AvailabilityCreate(BaseModel):
    event_id: UUID
    user_id: UUID
    start_time: datetime
    end_time: datetime
    status: str


class AvailabilityOut(BaseModel):
    availability_id: UUID
    event_id: UUID
    user_id: UUID
    start_time: datetime
    end_time: datetime
    status: str