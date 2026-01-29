# app/schemas/kiosk.py
from pydantic import BaseModel, ConfigDict, conint
from typing import Optional

PositiveInt = conint(gt=0)


class KioskBase(BaseModel):
    name: str
    floor_id: PositiveInt
    waypoint_id: Optional[str] = None
    description: Optional[str] = None


class KioskCreate(KioskBase):
    pass


class KioskUpdate(BaseModel):
    name: Optional[str] = None
    floor_id: Optional[PositiveInt] = None
    waypoint_id: Optional[str] = None
    description: Optional[str] = None


class Kiosk(KioskBase):
    id: PositiveInt

    model_config = ConfigDict(from_attributes=True)
