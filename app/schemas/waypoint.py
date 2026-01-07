

# app/schemas/waypoint.py
from pydantic import BaseModel
from typing import Optional
from app.models.waypoint import WaypointType

class WaypointBase(BaseModel):
    x: int
    y: int
    type: WaypointType
    label: Optional[str] = None
    connects_to_floor: Optional[int] = None
    connects_to_waypoint: Optional[str] = None

class WaypointCreate(WaypointBase):
    id: str
    floor_id: int

class WaypointUpdate(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    type: Optional[WaypointType] = None
    label: Optional[str] = None
    connects_to_floor: Optional[int] = None
    connects_to_waypoint: Optional[str] = None

class Waypoint(WaypointBase):
    id: str
    floor_id: int
    
    class Config:
        from_attributes = True
