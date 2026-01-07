
# app/api/navigation.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.pathfinding import PathFinder
from app.schemas.navigation import NavigationRequest, NavigationResponse, PathStep

router = APIRouter()

@router.post("/find-path", response_model=NavigationResponse)
def find_navigation_path(request: NavigationRequest, db: Session = Depends(get_db)):
    """Yo'l topish"""
    pathfinder = PathFinder(db)
    
    # Start va End waypoint larni aniqlash
    start_waypoint_id = request.start_waypoint_id
    end_waypoint_id = request.end_waypoint_id
    
    # Agar room_id berilgan bo'lsa, waypoint ga o'tkazish
    if request.start_room_id and not start_waypoint_id:
        start_waypoint_id = pathfinder.find_nearest_waypoint_to_room(request.start_room_id)
        if not start_waypoint_id:
            raise HTTPException(status_code=404, detail="Start room not found or has no waypoint")
    
    if request.end_room_id and not end_waypoint_id:
        end_waypoint_id = pathfinder.find_nearest_waypoint_to_room(request.end_room_id)
        if not end_waypoint_id:
            raise HTTPException(status_code=404, detail="End room not found or has no waypoint")
    
    # Agar kiosk_id berilgan bo'lsa, kiosk ning waypoint ini ishlatish
    if request.kiosk_id and not start_waypoint_id:
        # Bu yerda kiosk modelini qo'shish kerak
        # Hozircha placeholder
        pass
    
    if not start_waypoint_id or not end_waypoint_id:
        raise HTTPException(status_code=400, detail="Start and end waypoints required")
    
    # Yo'l topish
    path, total_distance = pathfinder.find_path(start_waypoint_id, end_waypoint_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="No path found")
    
    # Yo'riqnomalar qo'shish
    path = pathfinder.add_instructions(path)
    
    # Qavat o'zgarishlarini hisoblash
    floor_changes = 0
    for i in range(1, len(path)):
        if path[i]['floor_id'] != path[i-1]['floor_id']:
            floor_changes += 1
    
    # Vaqtni taxminiy hisoblash (50 units = 1 minut deb hisoblaymiz)
    estimated_time = total_distance / 50.0
    
    # PathStep objectlariga o'tkazish
    path_steps = [PathStep(**step) for step in path]
    
    return NavigationResponse(
        path=path_steps,
        total_distance=total_distance,
        floor_changes=floor_changes,
        estimated_time_minutes=estimated_time
    )

@router.get("/nearby-rooms/{waypoint_id}")
def get_nearby_rooms(waypoint_id: str, radius: int = 100, db: Session = Depends(get_db)):
    """Waypoint atrofidagi xonalarni topish"""
    from app.models.waypoint import Waypoint
    from app.models.room import Room
    import math
    
    waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    
    # Bir xil qavatdagi barcha xonalar
    rooms = db.query(Room).filter(Room.floor_id == waypoint.floor_id).all()
    
    nearby = []
    for room in rooms:
        if room.waypoint_id:
            room_wp = db.query(Waypoint).filter(Waypoint.id == room.waypoint_id).first()
            if room_wp:
                distance = math.sqrt(
                    (room_wp.x - waypoint.x)**2 + (room_wp.y - waypoint.y)**2
                )
                if distance <= radius:
                    nearby.append({
                        'room_id': room.id,
                        'name': room.name,
                        'distance': distance
                    })
    
    return nearby