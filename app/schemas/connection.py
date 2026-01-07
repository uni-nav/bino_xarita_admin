
# app/schemas/connection.py
from pydantic import BaseModel
from typing import Optional


class ConnectionBase(BaseModel):
    from_waypoint_id: str
    to_waypoint_id: str
    distance: float

class ConnectionCreate(ConnectionBase):
    id: Optional[str] = None # Endi bu majburiy emas

class Connection(ConnectionBase):
    id: Optional[str] = None
    
    class Config:
        from_attributes = True

