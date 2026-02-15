# app/models/kiosk.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Kiosk(Base):
    __tablename__ = "kiosks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    waypoint_id = Column(String(50), ForeignKey("waypoints.id", ondelete="SET NULL"), nullable=True)
    description = Column(String(255), nullable=True)

    floor = relationship("Floor", back_populates="kiosks")
    waypoint = relationship("Waypoint", back_populates="kiosks")
