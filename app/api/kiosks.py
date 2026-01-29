# app/api/kiosks.py
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.kiosk import Kiosk
from app.models.floor import Floor
from app.models.waypoint import Waypoint
from app.schemas.kiosk import Kiosk as KioskSchema, KioskCreate, KioskUpdate
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


def _validate_floor_waypoint_match(floor_id: int, waypoint: Waypoint) -> None:
    if waypoint.floor_id != floor_id:
        raise HTTPException(status_code=400, detail="Waypoint does not belong to the given floor")


@router.get("/", response_model=List[KioskSchema])
def get_kiosks(db: Session = Depends(get_db)):
    kiosks = db.query(Kiosk).all()
    return kiosks


@router.get("/{kiosk_id}", response_model=KioskSchema)
def get_kiosk(kiosk_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    kiosk = db.query(Kiosk).filter(Kiosk.id == kiosk_id).first()
    if not kiosk:
        raise HTTPException(status_code=404, detail="Kiosk not found")
    return kiosk


@router.post("/", response_model=KioskSchema)
def create_kiosk(
    kiosk: KioskCreate,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    _get_floor_or_404(db, kiosk.floor_id)
    if kiosk.waypoint_id:
        waypoint = _get_waypoint_or_404(db, kiosk.waypoint_id)
        _validate_floor_waypoint_match(kiosk.floor_id, waypoint)

    db_kiosk = Kiosk(**kiosk.model_dump())
    db.add(db_kiosk)
    db.commit()
    db.refresh(db_kiosk)
    return db_kiosk


@router.put("/{kiosk_id}", response_model=KioskSchema)
def update_kiosk(
    kiosk: KioskUpdate,
    kiosk_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    db_kiosk = db.query(Kiosk).filter(Kiosk.id == kiosk_id).first()
    if not db_kiosk:
        raise HTTPException(status_code=404, detail="Kiosk not found")

    update_data = kiosk.model_dump(exclude_unset=True)
    if "floor_id" in update_data and update_data["floor_id"] is not None:
        _get_floor_or_404(db, update_data["floor_id"])

    if "waypoint_id" in update_data and update_data["waypoint_id"] is not None:
        waypoint = _get_waypoint_or_404(db, update_data["waypoint_id"])
        floor_id = update_data.get("floor_id", db_kiosk.floor_id)
        _validate_floor_waypoint_match(floor_id, waypoint)

    for key, value in update_data.items():
        setattr(db_kiosk, key, value)

    db.commit()
    db.refresh(db_kiosk)
    return db_kiosk


@router.delete("/{kiosk_id}")
def delete_kiosk(
    kiosk_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)
):
    db_kiosk = db.query(Kiosk).filter(Kiosk.id == kiosk_id).first()
    if not db_kiosk:
        raise HTTPException(status_code=404, detail="Kiosk not found")

    db.delete(db_kiosk)
    db.commit()
    return {"message": "Kiosk deleted successfully"}
