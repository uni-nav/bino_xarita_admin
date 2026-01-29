
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.room import Room
from app.models.floor import Floor
from app.models.waypoint import Waypoint
from app.schemas.room import Room as RoomSchema, RoomCreate, RoomUpdate
from app.utils.room_parser import parse_room_name
from app.core.auth import verify_admin_token  # ✅ Admin auth

router = APIRouter()

def _get_floor_or_404(db: Session, floor_id: int) -> Floor:
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    return floor

@router.get("/", response_model=List[RoomSchema])
def get_rooms(
    skip: int = 0, 
    limit: int = 1000,
    floor_id: Optional[int] = None,
    building: Optional[str] = None,
    without_waypoint: bool = False,  # ← NEW: Nuqtasi yo'q xonalar
    db: Session = Depends(get_db)
):
    """Xonalarni olish"""
    query = db.query(Room)
    
    # Qavat bo'yicha filter
    if floor_id:
        _get_floor_or_404(db, floor_id)
        query = query.filter(Room.floor_id == floor_id)
    
    # Bino bo'yicha filter
    if building:
        query = query.filter(Room.name.contains(f"-{building} blok"))
    
    # Nuqtasi yo'q xonalar
    if without_waypoint:
        query = query.filter(Room.waypoint_id == None)
    
    rooms = query.offset(skip).limit(limit).all()
    return rooms

@router.get("/unassigned", response_model=List[RoomSchema])
def get_unassigned_rooms(
    floor_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Nuqta biriktirilmagan xonalar"""
    query = db.query(Room).filter(Room.waypoint_id == None)
    
    if floor_id:
        _get_floor_or_404(db, floor_id)
        query = query.filter(Room.floor_id == floor_id)
    
    return query.all()

@router.get("/search", response_model=List[RoomSchema])
def search_rooms(query: str, db: Session = Depends(get_db)):
    """Xonalarni qidirish"""
    normalized = query.strip()
    room_id = int(normalized) if normalized.isdigit() else None
    if room_id is not None:
        rooms = db.query(Room).filter(
            (Room.id == room_id) | (Room.name.ilike(f"%{normalized}%"))
        ).all()
    else:
        rooms = db.query(Room).filter(Room.name.ilike(f"%{normalized}%")).all()
    return rooms

@router.get("/{room_id}", response_model=RoomSchema)
def get_room(room_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Bitta xonani olish"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.post("/", response_model=RoomSchema)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Yangi xona yaratish"""
    # Parse qilish
    parsed = parse_room_name(room.name)
    
    # Agar floor_id berilmagan bo'lsa, parse dan olish
    floor_id = room.floor_id
    if not floor_id and parsed['floor_number']:
        # Floor_number ga mos keladigan qavatni topish
        floor = db.query(Floor).filter(
            Floor.floor_number == parsed['floor_number']
        ).first()
        if floor:
            floor_id = floor.id
    if floor_id:
        _get_floor_or_404(db, floor_id)
    
    db_room = Room(
        name=room.name,
        waypoint_id=room.waypoint_id,
        floor_id=floor_id
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.put("/{room_id}", response_model=RoomSchema)
def update_room(
    room: RoomUpdate,
    room_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Xonani yangilash"""
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    update_data = room.model_dump(exclude_unset=True)
    
    # Agar name yangilansa, floor_id ni ham yangilash
    if 'name' in update_data:
        parsed = parse_room_name(update_data['name'])
        if parsed['floor_number'] and 'floor_id' not in update_data:
            floor = db.query(Floor).filter(
                Floor.floor_number == parsed['floor_number']
            ).first()
            if floor:
                update_data['floor_id'] = floor.id
    if 'floor_id' in update_data and update_data['floor_id'] is not None:
        _get_floor_or_404(db, update_data['floor_id'])

    if 'waypoint_id' in update_data and update_data['waypoint_id'] is not None:
        waypoint = db.query(Waypoint).filter(Waypoint.id == update_data['waypoint_id']).first()
        if not waypoint:
            raise HTTPException(status_code=404, detail="Waypoint not found")
        target_floor_id = update_data.get('floor_id', db_room.floor_id)
        if target_floor_id and waypoint.floor_id != target_floor_id:
            raise HTTPException(status_code=400, detail="Waypoint does not belong to the room floor")
        if target_floor_id is None:
            update_data['floor_id'] = waypoint.floor_id
    
    for key, value in update_data.items():
        setattr(db_room, key, value)
    
    db.commit()
    db.refresh(db_room)
    return db_room

@router.patch("/{room_id}/assign-waypoint", response_model=RoomSchema)
def assign_waypoint_to_room(
    room_id: int = Path(..., gt=0),
    waypoint_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Xonaga waypoint biriktirish"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    if room.floor_id and waypoint.floor_id != room.floor_id:
        raise HTTPException(status_code=400, detail="Waypoint does not belong to the room floor")
    if room.floor_id is None:
        room.floor_id = waypoint.floor_id
    
    room.waypoint_id = waypoint_id
    db.commit()
    db.refresh(room)
    return room

@router.get("/floor/{floor_id}", response_model=List[RoomSchema])
def get_rooms_by_floor(floor_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Qavat bo'yicha xonalarni olish"""
    _get_floor_or_404(db, floor_id)
    rooms = db.query(Room).filter(Room.floor_id == floor_id).all()
    return rooms

@router.delete("/{room_id}")
def delete_room(
    room_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Xonani o'chirish"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    db.delete(room)
    db.commit()
    return {"message": "Room deleted successfully"}

@router.post("/auto-assign-floors")
def auto_assign_floors(
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """
    Barcha xonalarga avtomatik qavat belgilash
    Xona nomini parse qilib, mos keladigan qavatga biriktiradi
    """
    rooms = db.query(Room).filter(Room.floor_id == None).all()
    floors = db.query(Floor).all()
    
    updated_count = 0
    
    for room in rooms:
        parsed = parse_room_name(room.name)
        if parsed['floor_number']:
            # Mos keladigan qavatni topish
            floor = next(
                (f for f in floors if f.floor_number == parsed['floor_number']),
                None
            )
            if floor:
                room.floor_id = floor.id
                updated_count += 1
    
    db.commit()
    
    return {
        "message": f"{updated_count} xonaga qavat biriktirildi",
        "updated_count": updated_count
    }
