
from pydantic import BaseModel, Field
from typing import Optional
import re

class RoomBase(BaseModel):
    name: str
    waypoint_id: Optional[str] = None
    floor_id: Optional[int] = None

class RoomCreate(RoomBase):
    pass  # ID avtomatik generatsiya qilinadi (Integer)

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    waypoint_id: Optional[str] = None
    floor_id: Optional[int] = None

class Room(RoomBase):
    id: int  # ← Integer
    
    class Config:
        from_attributes = True
