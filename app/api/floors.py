# app/api/floors.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, cast
import shutil
import os
from datetime import datetime
from app.database import get_db
from app.models.floor import Floor
from app.schemas.floor import Floor as FloorSchema, FloorCreate, FloorUpdate
from app.core.config import settings
from app.core.auth import verify_admin_token  # ✅ Admin auth

router = APIRouter()

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
def create_floor(floor: FloorCreate, db: Session = Depends(get_db)):
    """Yangi qavat yaratish"""
    db_floor = Floor(**floor.dict())
    db.add(db_floor)
    db.commit()
    db.refresh(db_floor)
    return db_floor

@router.put("/{floor_id}", response_model=FloorSchema)
def update_floor(floor_id: int, floor: FloorUpdate, db: Session = Depends(get_db)):
    """Qavatni yangilash"""
    db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    
    for key, value in floor.dict(exclude_unset=True).items():
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
async def upload_floor_image(floor_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Qavat rasmini yuklash"""
    db_floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not db_floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    
    # Fayl formatini tekshirish
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    original_filename = file.filename or "image.jpg"

    # Fayl nomini yaratish
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(original_filename)[1]
    filename = f"floor_{floor_id}_{timestamp}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Faylni saqlash
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Rasm o'lchamini olish
    from PIL import Image
    with Image.open(file_path) as img:
        width, height = img.size
    
    # Database yangilash
    db_floor.image_url = f"/uploads/{filename}" # type: ignore
    db_floor.image_width = width # type: ignore
    db_floor.image_height = height # type: ignore
    db.commit()
    db.refresh(db_floor)
    
    return {"image_url": db_floor.image_url, "width": width, "height": height}
