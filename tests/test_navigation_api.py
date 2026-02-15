import pytest
from app.services.pathfinding import GraphCache

@pytest.fixture(autouse=True)
def clear_graph_cache():
    """Clear GraphCache before and after each test to ensure isolation"""
    GraphCache.get_instance().clear()
    yield
    GraphCache.get_instance().clear()

def create_floor(client, headers, floor_number=1, name="1-qavat"):
    resp = client.post(
        "/api/floors/",
        json={"name": name, "floor_number": floor_number},
        headers=headers,
    )
    assert resp.status_code == 200
    return resp.json()


def create_waypoint(
    client,
    headers,
    floor_id,
    waypoint_id,
    x=0,
    y=0,
    wp_type="hallway",
    label=None,
    connects_to_floor=None,
    connects_to_waypoint=None,
):
    payload = {
        "id": waypoint_id,
        "floor_id": floor_id,
        "x": x,
        "y": y,
        "type": wp_type,
        "label": label,
        "connects_to_floor": connects_to_floor,
        "connects_to_waypoint": connects_to_waypoint,
    }
    resp = client.post("/api/waypoints/", json=payload, headers=headers)
    assert resp.status_code == 200
    return resp.json()


def create_connection(client, headers, a, b, distance=10):
    resp = client.post(
        "/api/waypoints/connections",
        json={"from_waypoint_id": a, "to_waypoint_id": b, "distance": distance},
        headers=headers,
    )
    assert resp.status_code == 200
    return resp.json()


def create_room(client, headers, name, floor_id=None, waypoint_id=None):
    payload = {"name": name, "floor_id": floor_id, "waypoint_id": waypoint_id}
    resp = client.post("/api/rooms/", json=payload, headers=headers)
    assert resp.status_code == 200
    return resp.json()


def test_find_path_via_room_ids(client, auth_headers):
    floor = create_floor(client, auth_headers)

    room1 = create_room(client, auth_headers, "101-B blok", floor_id=floor["id"])
    room2 = create_room(client, auth_headers, "102-B blok", floor_id=floor["id"])

    wp1 = create_waypoint(client, auth_headers, floor["id"], "wp-r1", x=0, y=0, wp_type="room", label=room1["name"])
    wp2 = create_waypoint(client, auth_headers, floor["id"], "wp-r2", x=10, y=0, wp_type="room", label=room2["name"])
    create_connection(client, auth_headers, wp1["id"], wp2["id"], distance=10)

    # Attach rooms to their waypoints
    u1 = client.put(f"/api/rooms/{room1['id']}", json={"waypoint_id": wp1["id"]}, headers=auth_headers)
    assert u1.status_code == 200
    u2 = client.put(f"/api/rooms/{room2['id']}", json={"waypoint_id": wp2["id"]}, headers=auth_headers)
    assert u2.status_code == 200

    resp = client.post(
        "/api/navigation/find-path",
        json={"start_room_id": room1["id"], "end_room_id": room2["id"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_distance"] == 10.0
    assert [step["waypoint_id"] for step in data["path"]] == ["wp-r1", "wp-r2"]


def test_nearby_rooms_returns_rooms_within_radius(client, auth_headers):
    floor = create_floor(client, auth_headers)
    hall = create_waypoint(client, auth_headers, floor["id"], "wp-h", x=0, y=0, wp_type="hallway")

    room = create_room(client, auth_headers, "201-B blok", floor_id=floor["id"])
    room_wp = create_waypoint(client, auth_headers, floor["id"], "wp-room", x=3, y=4, wp_type="room", label=room["name"])
    u = client.put(f"/api/rooms/{room['id']}", json={"waypoint_id": room_wp["id"]}, headers=auth_headers)
    assert u.status_code == 200

    resp = client.get(f"/api/navigation/nearby-rooms/{hall['id']}", params={"radius": 5})
    assert resp.status_code == 200
    nearby = resp.json()
    assert len(nearby) == 1
    assert nearby[0]["room_id"] == room["id"]
    assert nearby[0]["distance"] == 5.0

