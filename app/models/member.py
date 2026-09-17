from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class MemberInvite(BaseModel):
    event_id: UUID
    user_id: UUID  # user yang diundang

class MemberStatusUpdate(BaseModel):
    member_status: str  # "joined" atau "declined"

class MemberOut(BaseModel):
    event_id: UUID
    user_id: UUID
    member_status: str
    joined_at: datetime