from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.database.models import ChallengeType

class ChallengeBase(BaseModel):
    name: str
    description: Optional[str] = None
    points: int
    type: ChallengeType
    is_active: bool = True

class ChallengeCreate(ChallengeBase):
    pass

class ChallengeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    points: Optional[int] = None
    type: Optional[ChallengeType] = None
    is_active: Optional[bool] = None

class ChallengeResponse(ChallengeBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
