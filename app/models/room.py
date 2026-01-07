
# app/models/room.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

class Room(Base):
    __tablename__ = "rooms"
    
    # Mavjud DB struktura
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # ← Integer, not String
    name = Column(String(100), nullable=False)  # ← "004-B blok" format
    
    # Yangi ustunlar (migration kerak)
    waypoint_id = Column(String(50), ForeignKey("waypoints.id", ondelete="SET NULL"), nullable=True)
    floor_id = Column(Integer, ForeignKey("floors.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    floor = relationship("Floor", back_populates="rooms")