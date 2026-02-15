import pytest
from app.services.pathfinding import PathFinder, GraphCache
from app.models.waypoint import Waypoint, WaypointType

@pytest.fixture(autouse=True)
def clear_graph_cache():
    """Clear GraphCache before and after each test to ensure isolation"""
    GraphCache.get_instance().clear()
    yield
    GraphCache.get_instance().clear()

from app.models.connection import Connection
from app.models.floor import Floor
from app.models.room import Room

def create_floor(db_session, floor_number=1, name="1-qavat"):
    floor = Floor(name=name, floor_number=floor_number)
    db_session.add(floor)
    db_session.commit()
    db_session.refresh(floor)
    return floor

def create_waypoint(db_session, floor_id, x=0, y=0, wp_id=None, wp_type=WaypointType.HALLWAY):
    if not wp_id:
        import uuid
        wp_id = str(uuid.uuid4())
    
    wp = Waypoint(
        id=wp_id,
        floor_id=floor_id,
        x=x,
        y=y,
        type=wp_type
    )
    db_session.add(wp)
    db_session.commit()
    return wp

def create_connection(db_session, wp1_id, wp2_id, distance=10.0):
    import uuid
    conn = Connection(
        id=str(uuid.uuid4()),
        from_waypoint_id=wp1_id,
        to_waypoint_id=wp2_id,
        distance=distance
    )
    db_session.add(conn)
    db_session.commit()
    return conn

def test_find_path_same_floor_direct(client, clean_db):
    """Test pathfinding between two connected waypoints on the same floor"""
    # Use clean_db fixture to ensure db is clean, but we need session
    # We can get session from testing session maker if needed, 
    # but conftest.py usually overrides get_db.
    # However, for service testing we need direct DB session access.
    # Let's use the functionality from conftest if exposed, strictly speaking 
    # we should likely instantiate PathFinder with a session.
    
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    
    try:
        # Setup
        floor = create_floor(db)
        wp1 = create_waypoint(db, floor.id, x=0, y=0, wp_id="wp1")
        wp2 = create_waypoint(db, floor.id, x=10, y=0, wp_id="wp2")
        create_connection(db, wp1.id, wp2.id, distance=10.0)
        
        # Test
        finder = PathFinder(db)
        path, distance = finder.find_path("wp1", "wp2")
        
        # Verify
        assert len(path) == 2
        assert path[0]['waypoint_id'] == "wp1"
        assert path[1]['waypoint_id'] == "wp2"
        assert distance == 10.0
        
    finally:
        db.close()

def test_find_path_same_floor_indirect(clean_db):
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    
    try:
        # Setup: wp1 -> wp2 -> wp3
        floor = create_floor(db)
        wp1 = create_waypoint(db, floor.id, x=0, y=0, wp_id="wp1")
        wp2 = create_waypoint(db, floor.id, x=10, y=0, wp_id="wp2")
        wp3 = create_waypoint(db, floor.id, x=20, y=0, wp_id="wp3")
        
        create_connection(db, wp1.id, wp2.id, 10.0)
        create_connection(db, wp2.id, wp3.id, 10.0)
        
        # Test
        finder = PathFinder(db)
        path, distance = finder.find_path("wp1", "wp3")
        
        # Verify
        assert len(path) == 3
        assert [p['waypoint_id'] for p in path] == ["wp1", "wp2", "wp3"]
        assert distance == 20.0
        
    finally:
        db.close()

def test_no_path_exists(clean_db):
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    
    try:
        floor = create_floor(db)
        wp1 = create_waypoint(db, floor.id, x=0, y=0, wp_id="wp1")
        wp2 = create_waypoint(db, floor.id, x=100, y=100, wp_id="wp2")
        # No connection
        
        finder = PathFinder(db)
        path, distance = finder.find_path("wp1", "wp2")
        
        assert path == []
        assert distance == float('inf')
        
    finally:
        db.close()

def test_find_path_multi_floor_stairs(clean_db):
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    
    try:
        # Floor 1
        f1 = create_floor(db, 1, "Floor 1")
        wp1 = create_waypoint(db, f1.id, 0, 0, "wp1_f1")
        stairs1 = create_waypoint(db, f1.id, 10, 0, "stairs_f1", WaypointType.STAIRS)
        
        # Floor 2
        f2 = create_floor(db, 2, "Floor 2")
        stairs2 = create_waypoint(db, f2.id, 10, 0, "stairs_f2", WaypointType.STAIRS)
        wp2 = create_waypoint(db, f2.id, 20, 0, "wp2_f2")
        
        # Connections
        create_connection(db, wp1.id, stairs1.id, 10.0)
        create_connection(db, stairs2.id, wp2.id, 10.0)
        
        # Connect stairs vertically
        stairs1.connects_to_waypoint = stairs2.id
        stairs1.connects_to_floor = f2.id
        stairs2.connects_to_waypoint = stairs1.id
        stairs2.connects_to_floor = f1.id
        db.commit()
        
        # Test
        finder = PathFinder(db)
        path, distance = finder.find_path("wp1_f1", "wp2_f2")
        
        # Should be: wp1 -> stairs1 -> stairs2 -> wp2
        assert len(path) == 4
        assert [p['waypoint_id'] for p in path] == ["wp1_f1", "stairs_f1", "stairs_f2", "wp2_f2"]
        # Distance: 10 + 50 (stairs cost) + 10 = 70.0
        # Wait, the heuristic adds cost, but the graph edge should also have cost.
        # In PathFinder.build_graph:
        # floor_change_cost = 50 if wp.type == WaypointType.STAIRS else 30
        # self.graph[wp.id].append((wp.connects_to_waypoint, floor_change_cost))
        
        # Our implementation creates directed edges for floor changes in `build_graph`.
        assert distance == 70.0
        
    finally:
        db.close()
