

# app/models/connection.py
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Connection(Base):
    __tablename__ = "connections"
    
    id = Column(String(50), primary_key=True, index=True)
    from_waypoint_id = Column(String(50), ForeignKey("waypoints.id", ondelete="CASCADE"), nullable=False)
    to_waypoint_id = Column(String(50), ForeignKey("waypoints.id", ondelete="CASCADE"), nullable=False)
    distance = Column(Float, nullable=False)
    
    from_waypoint = relationship("Waypoint", foreign_keys=[from_waypoint_id], back_populates="connections_from")
    to_waypoint = relationship("Waypoint", foreign_keys=[to_waypoint_id], back_populates="connections_to")


