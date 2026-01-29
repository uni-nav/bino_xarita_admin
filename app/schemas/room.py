
from pydantic import BaseModel, ConfigDict, conint
from typing import Optional

PositiveInt = conint(gt=0)

class RoomBase(BaseModel):
    name: str
    waypoint_id: Optional[str] = None
    floor_id: Optional[PositiveInt] = None

class RoomCreate(RoomBase):
    pass  # ID avtomatik generatsiya qilinadi (Integer)

class RoomUpdate(BaseModel):
    name: Optional[str] = None
    waypoint_id: Optional[str] = None
    floor_id: Optional[PositiveInt] = None

class Room(RoomBase):
    id: PositiveInt  # ← Integer
    
    model_config = ConfigDict(from_attributes=True)
