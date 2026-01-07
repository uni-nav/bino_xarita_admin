
# app/schemas/navigation.py
from pydantic import BaseModel
from typing import List, Optional

class NavigationRequest(BaseModel):
    start_waypoint_id: Optional[str] = None
    start_room_id: Optional[str] = None
    end_waypoint_id: Optional[str] = None
    end_room_id: Optional[str] = None
    kiosk_id: Optional[str] = None

class PathStep(BaseModel):
    waypoint_id: str
    floor_id: int
    x: int
    y: int
    type: str
    label: Optional[str] = None
    instruction: Optional[str] = None

class NavigationResponse(BaseModel):
    path: List[PathStep]
    total_distance: float
    floor_changes: int
    estimated_time_minutes: float
