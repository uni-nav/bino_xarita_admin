
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.room import Room
from app.models.floor import Floor
from app.schemas.room import Room as RoomSchema, RoomCreate, RoomUpdate
from app.utils.room_parser import parse_room_name

router = APIRouter()

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
        query = query.filter(Room.floor_id == floor_id)
    
    return query.all()

@router.get("/{room_id}", response_model=RoomSchema)
def get_room(room_id: int, db: Session = Depends(get_db)):
    """Bitta xonani olish"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.post("/", response_model=RoomSchema)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
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
def update_room(room_id: int, room: RoomUpdate, db: Session = Depends(get_db)):
    """Xonani yangilash"""
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    update_data = room.dict(exclude_unset=True)
    
    # Agar name yangilansa, floor_id ni ham yangilash
    if 'name' in update_data:
        parsed = parse_room_name(update_data['name'])
        if parsed['floor_number'] and 'floor_id' not in update_data:
            floor = db.query(Floor).filter(
                Floor.floor_number == parsed['floor_number']
            ).first()
            if floor:
                update_data['floor_id'] = floor.id
    
    for key, value in update_data.items():
        setattr(db_room, key, value)
    
    db.commit()
    db.refresh(db_room)
    return db_room

@router.patch("/{room_id}/assign-waypoint", response_model=RoomSchema)
def assign_waypoint_to_room(
    room_id: int,
    waypoint_id: str,
    db: Session = Depends(get_db)
):
    """Xonaga waypoint biriktirish"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room.waypoint_id = waypoint_id
    db.commit()
    db.refresh(room)
    return room

@router.get("/floor/{floor_id}", response_model=List[RoomSchema])
def get_rooms_by_floor(floor_id: int, db: Session = Depends(get_db)):
    """Qavat bo'yicha xonalarni olish"""
    rooms = db.query(Room).filter(Room.floor_id == floor_id).all()
    return rooms

@router.get("/search", response_model=List[RoomSchema])
def search_rooms(query: str, db: Session = Depends(get_db)):
    """Xonalarni qidirish"""
    rooms = db.query(Room).filter(
        (Room.id.ilike(f"%{query}%")) | (Room.name.ilike(f"%{query}%"))
    ).all()
    return rooms

@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    """Xonani o'chirish"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    db.delete(room)
    db.commit()
    return {"message": "Room deleted successfully"}

@router.post("/auto-assign-floors")
def auto_assign_floors(db: Session = Depends(get_db)):
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




# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import List, Optional
# from app.database import get_db
# from app.models.room import Room
# from pydantic import BaseModel

# router = APIRouter()

# class RoomBase(BaseModel):
#     name: str
#     capacity: Optional[int] = None
#     building: Optional[str] = None
#     waypoint_id: Optional[str] = None
#     floor_id: int

# class RoomCreate(RoomBase):
#     id: str

# class RoomSchema(RoomBase):
#     id: str
    
#     class Config:
#         from_attributes = True

# @router.get("/", response_model=List[RoomSchema])
# def get_rooms(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
#     """Barcha xonalarni olish"""
#     rooms = db.query(Room).offset(skip).limit(limit).all()
#     return rooms


# @router.get("/{room_id}", response_model=RoomSchema)
# def get_room(room_id: str, db: Session = Depends(get_db)):
#     """Bitta xonani olish"""
#     room = db.query(Room).filter(Room.id == room_id).first()
#     if not room:
#         raise HTTPException(status_code=404, detail="Room not found")
#     return room

# @router.post("/", response_model=RoomSchema)
# def create_room(room: RoomCreate, db: Session = Depends(get_db)):
#     """Yangi xona yaratish"""
#     db_room = Room(**room.dict())
#     db.add(db_room)
#     db.commit()
#     db.refresh(db_room)
#     return db_room

# @router.post("/batch", response_model=List[RoomSchema])
# def create_rooms_batch(rooms: List[RoomCreate], db: Session = Depends(get_db)):
#     """Ko'p xonalarni bir vaqtda yaratish"""
#     db_rooms = [Room(**room.dict()) for room in rooms]
#     db.add_all(db_rooms)
#     db.commit()
#     for room in db_rooms:
#         db.refresh(room)
#     return db_rooms

# @router.delete("/{room_id}")
# def delete_room(room_id: str, db: Session = Depends(get_db)):
#     """Xonani o'chirish"""
#     db_room = db.query(Room).filter(Room.id == room_id).first()
#     if not db_room:
#         raise HTTPException(status_code=404, detail="Room not found")
    
#     db.delete(db_room)
#     db.commit()
#     return {"message": "Room deleted successfully"}
