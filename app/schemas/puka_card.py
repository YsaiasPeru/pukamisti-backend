from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class PukaCardBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    rarity: str
    category: str

class PukaCardResponse(PukaCardBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
