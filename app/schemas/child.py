from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime

class ChildProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    birth_date: Optional[date] = None
    avatar: Optional[str] = None
    access_code: Optional[str] = None
    
    # Virtual fields to be computed by services
    level: Optional[str] = None
    league: Optional[str] = None
    total_points: Optional[int] = 0
    cards_collected: Optional[int] = 0
    total_cards: Optional[int] = 0
    challenges_completed: Optional[int] = 0

    class Config:
        from_attributes = True

class ChildCreateByParent(BaseModel):
    name: str
    pin: str
    birth_date: Optional[date] = None
    avatar: Optional[str] = None

class DailyConsumptionCreate(BaseModel):
    day_number: int
    is_consumed: bool = True

class DailyConsumptionResponse(BaseModel):
    id: UUID
    day_number: int
    is_consumed: bool
    points_earned: int
    registered_at: datetime

    class Config:
        from_attributes = True

class ChildStatsResponse(BaseModel):
    total_points: int
    level: str
    league: str
    cards_collected: int
    total_cards: int
    challenges_completed: int

class PlantPhotoUpload(BaseModel):
    stage: str # 'siembra', 'crecimiento', 'cosecha'
    photo_data: str

class RewardRedeemRequest(BaseModel):
    reward_id: str
    title: str
    cost: int
