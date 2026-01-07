
import re
from typing import Optional, Dict

def parse_room_name(room_name: str) -> Dict[str, Optional[str]]:
    """
    Xona nomini parse qilish
    Format: {qavat}{xona}-{blok}
    Misol: "106-B blok" → {floor: "1", room: "06", building: "B"}
    """
    # Pattern: 3 raqam (qavat + xona) - harf (blok)
    pattern = r'^(\d)(\d{2})-([A-Z])\s*blok$'
    match = re.match(pattern, room_name)
    
    if match:
        floor_num = match.group(1)
        room_num = match.group(2)
        building = match.group(3)
        
        return {
            'floor_number': int(floor_num),
            'room_number': room_num,
            'building': building,
            'floor_name': f"{floor_num}-qavat",
            'full_room': f"{floor_num}{room_num}",
        }
    
    return {
        'floor_number': None,
        'room_number': None,
        'building': None,
        'floor_name': None,
        'full_room': None,
    }

def format_room_name(floor_number: int, room_number: str, building: str) -> str:
    """
    Xona nomini format qilish
    Misol: (1, "06", "B") → "106-B blok"
    """
    return f"{floor_number}{room_number}-{building} blok"