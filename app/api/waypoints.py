
# app/api/waypoints.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.waypoint import Waypoint
from app.models.floor import Floor
from app.models.connection import Connection
from app.schemas.waypoint import Waypoint as WaypointSchema, WaypointCreate, WaypointUpdate
from app.schemas.connection import Connection as ConnectionSchema, ConnectionCreate
import uuid  # Fayl tepasiga qo'shing
from app.core.auth import verify_admin_token  # ✅ Admin auth

router = APIRouter()

def _get_floor_or_404(db: Session, floor_id: int) -> Floor:
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    return floor

def _get_waypoint_or_404(db: Session, waypoint_id: str) -> Waypoint:
    waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    return waypoint

def _normalize_pair(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a <= b else (b, a)

def _connection_exists(db: Session, a: str, b: str) -> bool:
    """
    Treat connections as undirected; disallow duplicates in either direction.
    """
    return (
        db.query(Connection)
        .filter(
            (Connection.from_waypoint_id == a) & (Connection.to_waypoint_id == b)
            | ((Connection.from_waypoint_id == b) & (Connection.to_waypoint_id == a))
        )
        .first()
        is not None
    )

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
def create_waypoint(
    waypoint: WaypointCreate,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Yangi nuqta yaratish"""
    _get_floor_or_404(db, waypoint.floor_id)
    if waypoint.connects_to_floor:
        _get_floor_or_404(db, waypoint.connects_to_floor)
    db_waypoint = Waypoint(**waypoint.model_dump())
    db.add(db_waypoint)
    db.commit()
    db.refresh(db_waypoint)
    return db_waypoint

@router.post("/batch", response_model=List[WaypointSchema])
def create_waypoints_batch(
    waypoints: List[WaypointCreate],
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Ko'p nuqtalarni bir vaqtda yaratish"""
    floor_ids = {wp.floor_id for wp in waypoints}
    for floor_id in floor_ids:
        _get_floor_or_404(db, floor_id)
    for wp in waypoints:
        if wp.connects_to_floor:
            _get_floor_or_404(db, wp.connects_to_floor)
    db_waypoints = [Waypoint(**wp.model_dump()) for wp in waypoints]
    db.add_all(db_waypoints)
    db.commit()
    for wp in db_waypoints:
        db.refresh(wp)
    return db_waypoints

@router.put("/{waypoint_id}", response_model=WaypointSchema)
def update_waypoint(
    waypoint_id: str,
    waypoint: WaypointUpdate,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Nuqtani yangilash"""
    db_waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not db_waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    if waypoint.connects_to_floor:
        _get_floor_or_404(db, waypoint.connects_to_floor)
    
    for key, value in waypoint.model_dump(exclude_unset=True).items():
        setattr(db_waypoint, key, value)
    
    db.commit()
    db.refresh(db_waypoint)
    return db_waypoint

@router.delete("/{waypoint_id}")
def delete_waypoint(
    waypoint_id: str,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Nuqtani o'chirish"""
    db_waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not db_waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    
    db.delete(db_waypoint)
    db.commit()
    return {"message": "Waypoint deleted successfully"}

# Connections
@router.post("/connections", response_model=ConnectionSchema)
def create_connection(
    connection: ConnectionCreate,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Bog'lanish yaratish"""
    if connection.from_waypoint_id == connection.to_waypoint_id:
        raise HTTPException(status_code=400, detail="Connection endpoints must be different")
    _get_waypoint_or_404(db, connection.from_waypoint_id)
    _get_waypoint_or_404(db, connection.to_waypoint_id)
    if _connection_exists(db, connection.from_waypoint_id, connection.to_waypoint_id):
        raise HTTPException(status_code=409, detail="Connection already exists")
    # Agar frontend ID yubormasa, o'zimiz yaratamiz
    connection_data = connection.model_dump()
    if not connection_data.get('id'):
        connection_data['id'] = str(uuid.uuid4())[:12] # Qisqa ID yaratish (12 belgi)
        
    db_connection = Connection(**connection_data)
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection

@router.post("/connections/batch", response_model=List[ConnectionSchema])
def create_connections_batch(
    connections: List[ConnectionCreate],
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Ko'p bog'lanishlarni bir vaqtda yaratish"""
    seen_pairs: set[tuple[str, str]] = set()
    for conn in connections:
        if conn.from_waypoint_id == conn.to_waypoint_id:
            raise HTTPException(status_code=400, detail="Connection endpoints must be different")
        _get_waypoint_or_404(db, conn.from_waypoint_id)
        _get_waypoint_or_404(db, conn.to_waypoint_id)
        pair = _normalize_pair(conn.from_waypoint_id, conn.to_waypoint_id)
        if pair in seen_pairs:
            raise HTTPException(status_code=400, detail="Duplicate connection in request")
        seen_pairs.add(pair)
        if _connection_exists(db, conn.from_waypoint_id, conn.to_waypoint_id):
            raise HTTPException(status_code=409, detail="Connection already exists")
    db_connections = []
    for conn in connections:
        conn_data = conn.model_dump()
        if not conn_data.get('id'):
            conn_data['id'] = str(uuid.uuid4())[:12]
        db_connections.append(Connection(**conn_data))
    db.add_all(db_connections)
    db.commit()
    for conn in db_connections:
        db.refresh(conn)
    return db_connections

@router.get("/connections/floor/{floor_id}", response_model=List[ConnectionSchema])
def get_connections_by_floor(floor_id: int, db: Session = Depends(get_db)):
    """Qavat bo'yicha bog'lanishlarni olish"""
    floor_waypoint_ids = db.query(Waypoint.id).filter(Waypoint.floor_id == floor_id)
    connections = db.query(Connection).filter(
        or_(
            Connection.from_waypoint_id.in_(floor_waypoint_ids),
            Connection.to_waypoint_id.in_(floor_waypoint_ids),
        )
    ).all()
    return connections

@router.delete("/connections/{connection_id}")
def delete_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Bog'lanishni o'chirish"""
    db_connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not db_connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(db_connection)
    db.commit()
    return {"message": "Connection deleted successfully"}
