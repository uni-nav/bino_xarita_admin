# app/api/floors.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, cast
import shutil
import os
import logging
from datetime import datetime, timezone
from app.database import get_db
from app.models.floor import Floor
from app.models.room import Room
from app.models.waypoint import Waypoint
from app.schemas.floor import Floor as FloorSchema, FloorCreate, FloorUpdate
from app.core.config import settings
from app.core.auth import verify_admin_token  # ✅ Admin auth
from PIL import Image, UnidentifiedImageError

router = APIRouter()
logger = logging.getLogger(__name__)


def _safe_unlink_upload_file(filename: str) -> None:
    """
    Best-effort deletion of a file under UPLOAD_DIR.
    Prevents path traversal by validating realpath containment.
    """
    upload_dir = os.path.realpath(settings.UPLOAD_DIR)
    candidate = os.path.realpath(os.path.join(settings.UPLOAD_DIR, filename))
    if not (candidate == upload_dir or candidate.startswith(upload_dir + os.sep)):
        logger.warning("Refusing to delete non-upload path: %s", candidate)
        return
    if os.path.exists(candidate):
        os.remove(candidate)

@router.get("/", response_model=List[FloorSchema])
def get_floors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Barcha qavatlarni olish"""
    floors = db.query(Floor).offset(skip).limit(limit).all()
    return floors

@router.get("/{floor_id}", response_model=FloorSchema)
def get_floor(floor_id: int, db: Session = Depends(get_db)):
    """Bitta qavatni olish"""
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    return floor

@router.post("/", response_model=FloorSchema)
def create_floor(
    floor: FloorCreate,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Yangi qavat yaratish"""
    db_floor = Floor(**floor.model_dump())
    if db_floor.created_at is None:
        db_floor.created_at = datetime.now(timezone.utc)
    db.add(db_floor)
    db.commit()
    db.refresh(db_floor)
    return db_floor

@router.put("/{floor_id}", response_model=FloorSchema)
def update_floor(
    floor_id: int,
    floor: FloorUpdate,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Qavatni yangilash"""
    db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    
    for key, value in floor.model_dump(exclude_unset=True).items():
        setattr(db_floor, key, value)
    
    db.commit()
    db.refresh(db_floor)
    return db_floor

@router.delete("/{floor_id}")
def delete_floor(
    floor_id: int,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)  # ✅ Admin authentication required
):
    """Qavatni o'chirish (Admin only)"""
    db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")

    # Detach rooms first (rooms should survive floor deletion)
    # - Null out floor_id for rooms on this floor
    # - Also null out waypoint_id, since floor waypoints will be deleted
    db.query(Room).filter(Room.floor_id == floor_id).update(
        {Room.floor_id: None, Room.waypoint_id: None},
        synchronize_session=False,
    )
    floor_waypoint_ids = db.query(Waypoint.id).filter(Waypoint.floor_id == floor_id)
    db.query(Room).filter(Room.waypoint_id.in_(floor_waypoint_ids)).update(
        {Room.waypoint_id: None},
        synchronize_session=False,
    )
    
    # Rasmni o'chirish
    if db_floor.image_url is not None:
        img_url = str(db_floor.image_url)
        image_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(img_url))
        if os.path.exists(image_path):
            os.remove(image_path)
    
    
    db.delete(db_floor)
    db.commit()
    return {"message": "Floor deleted successfully"}

@router.post("/{floor_id}/upload-image")
async def upload_floor_image(
    floor_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    """Qavat rasmini yuklash"""
    db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    
    # Fayl formatini tekshirish
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Allowable extensions
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
         raise HTTPException(status_code=400, detail="Invalid file extension")

    # Fayl hajmini tekshirish (MB)
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    try:
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
    except Exception:
        size = 0
    if size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large. Max {settings.MAX_UPLOAD_MB} MB",
        )
    
    original_filename = file.filename or "image.jpg"

    old_image_filename: str | None = None
    if db_floor.image_url:
        try:
            old_basename = os.path.basename(str(db_floor.image_url))
            if old_basename:
                old_image_filename = old_basename
        except Exception:
            old_image_filename = None

    # Fayl nomini yaratish
    # Use microseconds to avoid collisions on quick successive uploads
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    file_extension = os.path.splitext(original_filename)[1]
    filename = f"floor_{floor_id}_{timestamp}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Faylni saqlash
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Rasm o'lchamini olish
    try:
        with Image.open(file_path) as img:
            width, height = img.size
    except UnidentifiedImageError:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail="Invalid image file")
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to process image")
    
    # Database yangilash
    db_floor.image_url = f"/api/uploads/{filename}" # type: ignore
    db_floor.image_width = width # type: ignore
    db_floor.image_height = height # type: ignore
    db.commit()
    db.refresh(db_floor)

    # Best-effort: delete previous image after successfully saving and updating DB
    if old_image_filename and old_image_filename != filename:
        try:
            _safe_unlink_upload_file(old_image_filename)
        except Exception as e:
            logger.warning("Failed to delete old floor image '%s': %s", old_image_filename, e)
    
    return {"image_url": db_floor.image_url, "width": width, "height": height}
