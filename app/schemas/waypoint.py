

# app/schemas/waypoint.py
from pydantic import BaseModel, ConfigDict, conint
from typing import Optional
from app.models.waypoint import WaypointType

PositiveInt = conint(gt=0)
NonNegativeInt = conint(ge=0)

class WaypointBase(BaseModel):
    x: NonNegativeInt
    y: NonNegativeInt
    type: WaypointType
    label: Optional[str] = None
    connects_to_floor: Optional[NonNegativeInt] = None
    connects_to_waypoint: Optional[str] = None

class WaypointCreate(WaypointBase):
    id: str
    floor_id: PositiveInt

class WaypointUpdate(BaseModel):
    x: Optional[NonNegativeInt] = None
    y: Optional[NonNegativeInt] = None
    type: Optional[WaypointType] = None
    label: Optional[str] = None
    connects_to_floor: Optional[NonNegativeInt] = None
    connects_to_waypoint: Optional[str] = None

class Waypoint(WaypointBase):
    id: str
    floor_id: PositiveInt
    
    model_config = ConfigDict(from_attributes=True)
