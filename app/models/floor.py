
# app/models/floor.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Floor(Base):
    __tablename__ = "floors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    floor_number = Column(Integer, nullable=False)
    image_url = Column(String(255), nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    waypoints = relationship("Waypoint",       
                foreign_keys="[Waypoint.floor_id]",
                back_populates="floor", 
                cascade="all, delete-orphan"
                )
    rooms = relationship("Room", back_populates="floor", cascade="all, delete-orphan")
    kiosks = relationship("Kiosk", back_populates="floor", cascade="all, delete-orphan")


