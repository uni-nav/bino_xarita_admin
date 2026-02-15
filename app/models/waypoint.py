
# app/models/waypoint.py
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum
from app.database import Base

class WaypointType(str, Enum):
    HALLWAY = "hallway"
    ROOM = "room"
    STAIRS = "stairs"
    ELEVATOR = "elevator"
    HALL = "hall"

class Waypoint(Base):
    __tablename__ = "waypoints"
    
    id = Column(String(50), primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="CASCADE"), nullable=False, index=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    type = Column(SQLEnum(WaypointType), nullable=False)
    label = Column(String(100), nullable=True)
    connects_to_floor = Column(Integer, ForeignKey("floors.id"), nullable=True)
    connects_to_waypoint = Column(String(50), nullable=True)
    
    floor = relationship("Floor", foreign_keys=[floor_id], back_populates="waypoints")
    connections_from = relationship("Connection", foreign_keys="Connection.from_waypoint_id", 
                                   back_populates="from_waypoint", cascade="all, delete-orphan")
    connections_to = relationship("Connection", foreign_keys="Connection.to_waypoint_id",
                                 back_populates="to_waypoint", cascade="all, delete-orphan")
    kiosks = relationship("Kiosk", back_populates="waypoint")
