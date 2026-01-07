
# app/api/waypoints.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.waypoint import Waypoint
from app.models.connection import Connection
from app.schemas.waypoint import Waypoint as WaypointSchema, WaypointCreate, WaypointUpdate
from app.schemas.connection import Connection as ConnectionSchema, ConnectionCreate
import uuid  # Fayl tepasiga qo'shing

router = APIRouter()

@router.get("/floor/{floor_id}", response_model=List[WaypointSchema])
def get_waypoints_by_floor(floor_id: int, db: Session = Depends(get_db)):
    """Qavat bo'yicha nuqtalarni olish"""
    waypoints = db.query(Waypoint).filter(Waypoint.floor_id == floor_id).all()
    return waypoints

@router.get("/{waypoint_id}", response_model=WaypointSchema)
def get_waypoint(waypoint_id: str, db: Session = Depends(get_db)):
    """Bitta nuqtani olish"""
    waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    return waypoint

@router.post("/", response_model=WaypointSchema)
def create_waypoint(waypoint: WaypointCreate, db: Session = Depends(get_db)):
    """Yangi nuqta yaratish"""
    db_waypoint = Waypoint(**waypoint.dict())
    db.add(db_waypoint)
    db.commit()
    db.refresh(db_waypoint)
    return db_waypoint

@router.post("/batch", response_model=List[WaypointSchema])
def create_waypoints_batch(waypoints: List[WaypointCreate], db: Session = Depends(get_db)):
    """Ko'p nuqtalarni bir vaqtda yaratish"""
    db_waypoints = [Waypoint(**wp.dict()) for wp in waypoints]
    db.add_all(db_waypoints)
    db.commit()
    for wp in db_waypoints:
        db.refresh(wp)
    return db_waypoints

@router.put("/{waypoint_id}", response_model=WaypointSchema)
def update_waypoint(waypoint_id: str, waypoint: WaypointUpdate, db: Session = Depends(get_db)):
    """Nuqtani yangilash"""
    db_waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not db_waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    
    for key, value in waypoint.dict(exclude_unset=True).items():
        setattr(db_waypoint, key, value)
    
    db.commit()
    db.refresh(db_waypoint)
    return db_waypoint

@router.delete("/{waypoint_id}")
def delete_waypoint(waypoint_id: str, db: Session = Depends(get_db)):
    """Nuqtani o'chirish"""
    db_waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not db_waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    
    db.delete(db_waypoint)
    db.commit()
    return {"message": "Waypoint deleted successfully"}

# Connections
@router.post("/connections", response_model=ConnectionSchema)
def create_connection(connection: ConnectionCreate, db: Session = Depends(get_db)):
    """Bog'lanish yaratish"""
    # Agar frontend ID yubormasa, o'zimiz yaratamiz
    connection_data = connection.dict()
    if not connection_data.get('id'):
        connection_data['id'] = str(uuid.uuid4())[:8] # Qisqa ID yaratish
        
    db_connection = Connection(**connection_data)
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection

@router.post("/connections/batch", response_model=List[ConnectionSchema])
def create_connections_batch(connections: List[ConnectionCreate], db: Session = Depends(get_db)):
    """Ko'p bog'lanishlarni bir vaqtda yaratish"""
    db_connections = [Connection(**conn.dict()) for conn in connections]
    db.add_all(db_connections)
    db.commit()
    for conn in db_connections:
        db.refresh(conn)
    return db_connections

@router.get("/connections/floor/{floor_id}", response_model=List[ConnectionSchema])
def get_connections_by_floor(floor_id: int, db: Session = Depends(get_db)):
    """Qavat bo'yicha bog'lanishlarni olish"""
    connections = db.query(Connection).join(
        Waypoint, Connection.from_waypoint_id == Waypoint.id
    ).filter(Waypoint.floor_id == floor_id).all()
    return connections

@router.delete("/connections/{connection_id}")
def delete_connection(connection_id: str, db: Session = Depends(get_db)):
    """Bog'lanishni o'chirish"""
    db_connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not db_connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(db_connection)
    db.commit()
    return {"message": "Connection deleted successfully"}
