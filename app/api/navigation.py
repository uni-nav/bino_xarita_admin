
# app/api/navigation.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.pathfinding import PathFinder
from app.schemas.navigation import NavigationRequest, NavigationResponse, PathStep
from app.models.kiosk import Kiosk
from app.models.floor import Floor
from app.models.waypoint import Waypoint, WaypointType
from app.models.connection import Connection
from app.core.auth import verify_admin_token
from app.models.room import Room
import math
    
router = APIRouter()

@router.post("/find-path", response_model=NavigationResponse)
def find_navigation_path(request: NavigationRequest, db: Session = Depends(get_db)):
    """Yo'l topish"""
    pathfinder = PathFinder(db)
    
    # Start va End waypoint larni aniqlash
    start_waypoint_id = request.start_waypoint_id
    end_waypoint_id = request.end_waypoint_id
    
    # Agar room_id berilgan bo'lsa, waypoint ga o'tkazish
    if request.start_room_id is not None and not start_waypoint_id:
        start_waypoint_id = pathfinder.find_nearest_waypoint_to_room(request.start_room_id)
        if not start_waypoint_id:
            raise HTTPException(status_code=404, detail="Start room not found or has no waypoint")
    
    if request.end_room_id is not None and not end_waypoint_id:
        end_waypoint_id = pathfinder.find_nearest_waypoint_to_room(request.end_room_id)
        if not end_waypoint_id:
            raise HTTPException(status_code=404, detail="End room not found or has no waypoint")
    
    # Agar kiosk_id berilgan bo'lsa, kiosk ning waypoint ini ishlatish
    if request.kiosk_id and not start_waypoint_id:
        kiosk = db.query(Kiosk).filter(Kiosk.id == request.kiosk_id).first()
        if kiosk and kiosk.waypoint_id:
            start_waypoint_id = kiosk.waypoint_id
        elif kiosk:
            raise HTTPException(status_code=400, detail="Kiosk has no waypoint assigned")
        else:
            raise HTTPException(status_code=404, detail="Kiosk not found")
    
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
    waypoint = db.query(Waypoint).filter(Waypoint.id == waypoint_id).first()
    if not waypoint:
        raise HTTPException(status_code=404, detail="Waypoint not found")
    
    # Bir xil qavatdagi barcha xonalar va ularning waypointlarini olish (JOIN)
    # N+1 query muammosini oldini olish
    rooms_data = (
        db.query(Room, Waypoint)
        .join(Waypoint, Room.waypoint_id == Waypoint.id)
        .filter(Room.floor_id == waypoint.floor_id)
        .all()
    )
    
    nearby = []
    for room, room_wp in rooms_data:
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


@router.get("/audit")
def audit_map(db: Session = Depends(get_db), _token: str = Depends(verify_admin_token)):
    """
    Admin-only map audit:
    - Check disconnected components
    - Detect one-way legacy connects_to_waypoint links
    - Find stairs/elevators without cross-floor links
    """
    floors = db.query(Floor).all()
    waypoints = db.query(Waypoint).all()
    connections = db.query(Connection).all()

    floor_by_id: Dict[int, Floor] = {f.id: f for f in floors}
    wp_by_id: Dict[str, Waypoint] = {w.id: w for w in waypoints}

    def floor_info(fid: int) -> Dict[str, Any]:
        floor = floor_by_id.get(fid)
        return {
            "id": fid,
            "floor_number": floor.floor_number if floor else None,
            "name": floor.name if floor else None,
        }

    # Build undirected adjacency for component detection
    adjacency: Dict[str, Set[str]] = {w.id: set() for w in waypoints}
    connections_by_wp: Dict[str, Set[str]] = {w.id: set() for w in waypoints}
    missing_waypoints_in_connections: List[Dict[str, Any]] = []

    for conn in connections:
        if conn.from_waypoint_id not in wp_by_id or conn.to_waypoint_id not in wp_by_id:
            missing_waypoints_in_connections.append(
                {
                    "connection_id": conn.id,
                    "from_waypoint_id": conn.from_waypoint_id,
                    "to_waypoint_id": conn.to_waypoint_id,
                }
            )
            continue
        adjacency[conn.from_waypoint_id].add(conn.to_waypoint_id)
        adjacency[conn.to_waypoint_id].add(conn.from_waypoint_id)
        connections_by_wp[conn.from_waypoint_id].add(conn.to_waypoint_id)
        connections_by_wp[conn.to_waypoint_id].add(conn.from_waypoint_id)

    legacy_one_way_links: List[Dict[str, Any]] = []
    for wp in waypoints:
        if not wp.connects_to_waypoint:
            continue
        target = wp_by_id.get(wp.connects_to_waypoint)
        if not target:
            legacy_one_way_links.append(
                {
                    "waypoint_id": wp.id,
                    "floor": floor_info(wp.floor_id),
                    "connects_to_waypoint": wp.connects_to_waypoint,
                    "issue": "target_missing",
                }
            )
            continue
        # Add undirected edge for component detection
        adjacency[wp.id].add(target.id)
        adjacency[target.id].add(wp.id)
        if target.connects_to_waypoint != wp.id:
            legacy_one_way_links.append(
                {
                    "waypoint_id": wp.id,
                    "floor": floor_info(wp.floor_id),
                    "connects_to_waypoint": target.id,
                    "issue": "reverse_missing",
                }
            )

    # Connected components (undirected)
    visited: Set[str] = set()
    components: List[Dict[str, Any]] = []
    for wp_id in adjacency.keys():
        if wp_id in visited:
            continue
        stack = [wp_id]
        comp_nodes: List[str] = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            comp_nodes.append(current)
            for nxt in adjacency.get(current, set()):
                if nxt not in visited:
                    stack.append(nxt)
        comp_floor_ids = sorted({wp_by_id[n].floor_id for n in comp_nodes if n in wp_by_id})
        comp_floor_numbers = [
            floor_by_id[fid].floor_number for fid in comp_floor_ids if fid in floor_by_id
        ]
        components.append(
            {
                "component_id": len(components) + 1,
                "waypoint_count": len(comp_nodes),
                "floor_ids": comp_floor_ids,
                "floor_numbers": comp_floor_numbers,
            }
        )

    floors_with_no_waypoints = [
        floor_info(f.id) for f in floors if not any(w.floor_id == f.id for w in waypoints)
    ]

    # Floors not connected to the largest component
    disconnected_floors: List[Dict[str, Any]] = []
    if components:
        largest = max(components, key=lambda c: c["waypoint_count"])
        connected_floor_ids = set(largest["floor_ids"])
        for f in floors:
            if f.id not in connected_floor_ids and any(w.floor_id == f.id for w in waypoints):
                disconnected_floors.append(floor_info(f.id))

    # Stairs/elevators without cross-floor links (connections or legacy)
    stairs_without_vertical_links: List[Dict[str, Any]] = []
    for wp in waypoints:
        if wp.type not in (WaypointType.STAIRS, WaypointType.ELEVATOR):
            continue
        has_vertical = False
        for other_id in connections_by_wp.get(wp.id, set()):
            other = wp_by_id.get(other_id)
            if other and other.floor_id != wp.floor_id:
                has_vertical = True
                break
        if not has_vertical and wp.connects_to_waypoint:
            target = wp_by_id.get(wp.connects_to_waypoint)
            if target and target.floor_id != wp.floor_id:
                has_vertical = True
        if not has_vertical:
            stairs_without_vertical_links.append(
                {
                    "waypoint_id": wp.id,
                    "type": wp.type.value,
                    "floor": floor_info(wp.floor_id),
                }
            )

    return {
        "summary": {
            "floors": len(floors),
            "waypoints": len(waypoints),
            "connections": len(connections),
            "components": len(components),
            "disconnected_floors": disconnected_floors,
            "floors_with_no_waypoints": floors_with_no_waypoints,
            "legacy_one_way_links": len(legacy_one_way_links),
            "stairs_without_vertical_links": len(stairs_without_vertical_links),
        },
        "components": components,
        "issues": {
            "legacy_one_way_links": legacy_one_way_links,
            "stairs_without_vertical_links": stairs_without_vertical_links,
            "missing_waypoints_in_connections": missing_waypoints_in_connections,
        },
    }
