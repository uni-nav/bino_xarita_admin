
# app/schemas/floor.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FloorBase(BaseModel):
    name: str
    floor_number: int
    image_url: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None

class FloorCreate(FloorBase):
    pass

class FloorUpdate(BaseModel):
    name: Optional[str] = None
    floor_number: Optional[int] = None
    image_url: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None

class Floor(FloorBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
