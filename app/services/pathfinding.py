# app/services/pathfinding.py
import heapq
import math
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.waypoint import Waypoint, WaypointType
from app.models.connection import Connection
from app.models.room import Room

class PathNode:
    """Yo'l topish uchun node struktura"""
    def __init__(self, waypoint_id: str, floor_id: int, x: int, y: int, 
                 g_score: float, f_score: float, parent: Optional['PathNode'] = None):
        self.waypoint_id = waypoint_id
        self.floor_id = floor_id
        self.x = x
        self.y = y
        self.g_score = g_score  # Boshlanishdan bu node gacha masofa
        self.f_score = f_score  # g_score + heuristic (taxminiy masofa maqsadgacha)
        self.parent = parent
    
    def __lt__(self, other):
        return self.f_score < other.f_score
    
    def __eq__(self, other):
        return self.waypoint_id == other.waypoint_id

class PathFinder:
    """A* algoritmi bilan yo'l topish"""
    
    def __init__(self, db: Session):
        self.db = db
        self.graph = None
        self.waypoints_dict = {}
    
    def build_graph(self):
        """Grafni qurish - barcha waypoints va connections"""
        if self.graph is not None:
            return
        
        # Barcha waypoints va connections ni olish
        waypoints = self.db.query(Waypoint).all()
        connections = self.db.query(Connection).all()
        
        # Graph yaratish: {waypoint_id: [(neighbor_id, distance), ...]}
        self.graph = {wp.id: [] for wp in waypoints}
        self.waypoints_dict = {wp.id: wp for wp in waypoints}
        
        # Bog'lanishlarni qo'shish (ikki tomonlama)
        for conn in connections:
            self.graph[conn.from_waypoint_id].append((conn.to_waypoint_id, conn.distance))
            self.graph[conn.to_waypoint_id].append((conn.from_waypoint_id, conn.distance))
        
        # Zinalar va liftlar uchun qavat o'tishlarini qo'shish
        for wp in waypoints:
            if wp.type in [WaypointType.STAIRS, WaypointType.ELEVATOR]:
                if wp.connects_to_waypoint:
                    # Qavat o'tish - qo'shimcha vaqt/masofa
                    floor_change_cost = 50 if wp.type == WaypointType.STAIRS else 30
                    self.graph[wp.id].append((wp.connects_to_waypoint, floor_change_cost))
    
    def heuristic(self, wp1_id: str, wp2_id: str) -> float:
        """Heuristic funksiya - Euclidean distance + qavat o'zgarishi"""
        wp1 = self.waypoints_dict.get(wp1_id)
        wp2 = self.waypoints_dict.get(wp2_id)
        
        if not wp1 or not wp2:
            return float('inf')
        
        # Bir xil qavatda bo'lsa - oddiy Euclidean distance
        if wp1.floor_id == wp2.floor_id:
            return math.sqrt((wp2.x - wp1.x)**2 + (wp2.y - wp1.y)**2)
        
        # Turli qavatlarda bo'lsa - taxminiy masofa + qavat o'zgarishi
        floor_diff = abs(wp2.floor_id - wp1.floor_id)
        base_distance = math.sqrt((wp2.x - wp1.x)**2 + (wp2.y - wp1.y)**2)
        return base_distance + (floor_diff * 100)  # Har bir qavat uchun 100 unit qo'shamiz
    
    def reconstruct_path(self, end_node: PathNode) -> List[Dict]:
        """Yo'lni qayta qurish"""
        path = []
        current = end_node
        
        while current is not None:
            wp = self.waypoints_dict[current.waypoint_id]
            path.append({
                'waypoint_id': current.waypoint_id,
                'floor_id': current.floor_id,
                'x': current.x,
                'y': current.y,
                'type': wp.type.value,
                'label': wp.label
            })
            current = current.parent
        
        path.reverse()
        return path
    
    def find_path(self, start_id: str, end_id: str) -> Tuple[List[Dict], float]:
        """
        A* algoritmi bilan yo'l topish
        Returns: (path, total_distance)
        """
        self.build_graph()
        
        if start_id not in self.graph or end_id not in self.graph:
            return [], float('inf')
        
        if start_id == end_id:
            start_wp = self.waypoints_dict[start_id]
            return [{
                'waypoint_id': start_id,
                'floor_id': start_wp.floor_id,
                'x': start_wp.x,
                'y': start_wp.y,
                'type': start_wp.type.value,
                'label': start_wp.label
            }], 0.0
        
        # A* algoritmi
        start_wp = self.waypoints_dict[start_id]
        start_node = PathNode(
            start_id, start_wp.floor_id, start_wp.x, start_wp.y,
            g_score=0,
            f_score=self.heuristic(start_id, end_id)
        )
        
        open_set = [start_node]  # Priority queue
        closed_set = set()
        g_scores = {start_id: 0}
        
        while open_set:
            current = heapq.heappop(open_set)
            
            if current.waypoint_id == end_id:
                path = self.reconstruct_path(current)
                return path, current.g_score
            
            if current.waypoint_id in closed_set:
                continue
            
            closed_set.add(current.waypoint_id)
            
            # Qo'shnilarni tekshirish
            for neighbor_id, distance in self.graph[current.waypoint_id]:
                if neighbor_id in closed_set:
                    continue
                
                tentative_g_score = current.g_score + distance
                
                if neighbor_id not in g_scores or tentative_g_score < g_scores[neighbor_id]:
                    g_scores[neighbor_id] = tentative_g_score
                    neighbor_wp = self.waypoints_dict[neighbor_id]
                    f_score = tentative_g_score + self.heuristic(neighbor_id, end_id)
                    
                    neighbor_node = PathNode(
                        neighbor_id, neighbor_wp.floor_id, 
                        neighbor_wp.x, neighbor_wp.y,
                        g_score=tentative_g_score,
                        f_score=f_score,
                        parent=current
                    )
                    heapq.heappush(open_set, neighbor_node)
        
        return [], float('inf')  # Yo'l topilmadi
    
    def add_instructions(self, path: List[Dict]) -> List[Dict]:
        """Yo'lga yo'riqnomalar qo'shish"""
        if len(path) <= 1:
            return path
        
        for i, step in enumerate(path):
            if i == 0:
                step['instruction'] = "Boshlanish nuqtasi"
            elif i == len(path) - 1:
                step['instruction'] = "Maqsadga yetdingiz"
            else:
                prev_step = path[i-1]
                next_step = path[i+1]
                
                # Qavat o'zgarishini aniqlash
                if step['floor_id'] != prev_step['floor_id']:
                    if step['type'] == 'stairs':
                        direction = "yuqoriga" if step['floor_id'] > prev_step['floor_id'] else "pastga"
                        step['instruction'] = f"Zina orqali {direction} chiqing"
                    elif step['type'] == 'elevator':
                        step['instruction'] = f"Liftda {step['floor_id']}-qavatga chiqing"
                else:
                    # Yo'nalishni hisoblash
                    angle1 = math.atan2(step['y'] - prev_step['y'], step['x'] - prev_step['x'])
                    angle2 = math.atan2(next_step['y'] - step['y'], next_step['x'] - step['x'])
                    angle_diff = math.degrees(angle2 - angle1) % 360
                    
                    if angle_diff < 45 or angle_diff > 315:
                        step['instruction'] = "To'g'ri davom eting"
                    elif 45 <= angle_diff < 135:
                        step['instruction'] = "Chapga buriling"
                    elif 225 < angle_diff <= 315:
                        step['instruction'] = "O'ngga buriling"
                    else:
                        step['instruction'] = "Orqaga buriling"
        
        return path
    
    def find_nearest_waypoint_to_room(self, room_id: str) -> Optional[str]:
        """Xonaga eng yaqin waypoint topish"""
        room = self.db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return None
        
        # Agar xonaga waypoint biriktirilgan bo'lsa
        if room.waypoint_id:
            return room.waypoint_id
        
        # Aks holda, bir xil qavatdagi eng yaqin waypoint ni topish
        waypoints = self.db.query(Waypoint).filter(
            Waypoint.floor_id == room.floor_id,
            Waypoint.type == WaypointType.ROOM
        ).all()
        
        # Bu yerda mantiqiy topish kerak - hozircha birinchisini qaytaramiz
        if waypoints:
            return waypoints[0].id
        
        return None
