def create_floor(client, headers, name="1-qavat", floor_number=1):
    response = client.post(
        "/api/floors/",
        json={"name": name, "floor_number": floor_number},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def create_waypoint(client, headers, floor_id, waypoint_id="wp-1"):
    response = client.post(
        "/api/waypoints/",
        json={
            "id": waypoint_id,
            "floor_id": floor_id,
            "x": 10,
            "y": 20,
            "type": "room",
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_kiosk_crud_success(client, auth_headers):
    floor = create_floor(client, auth_headers, floor_number=1)
    waypoint = create_waypoint(client, auth_headers, floor_id=floor["id"])

    # Create
    create_resp = client.post(
        "/api/kiosks/",
        json={
            "name": "Kiosk A",
            "floor_id": floor["id"],
            "waypoint_id": waypoint["id"],
            "description": "Main entrance",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 200
    kiosk = create_resp.json()
    assert kiosk["name"] == "Kiosk A"
    assert kiosk["floor_id"] == floor["id"]
    assert kiosk["waypoint_id"] == waypoint["id"]

    # Get
    get_resp = client.get(f"/api/kiosks/{kiosk['id']}")
    assert get_resp.status_code == 200

    # Update
    update_resp = client.put(
        f"/api/kiosks/{kiosk['id']}",
        json={"name": "Kiosk B", "description": "Updated"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Kiosk B"

    # List
    list_resp = client.get("/api/kiosks/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Delete
    delete_resp = client.delete(f"/api/kiosks/{kiosk['id']}", headers=auth_headers)
    assert delete_resp.status_code == 200

    # Get after delete
    get_deleted = client.get(f"/api/kiosks/{kiosk['id']}")
    assert get_deleted.status_code == 404


def test_kiosk_create_invalid_floor(client, auth_headers):
    response = client.post(
        "/api/kiosks/",
        json={"name": "Invalid", "floor_id": 999, "waypoint_id": None},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_kiosk_create_mismatched_waypoint_floor(client, auth_headers):
    floor1 = create_floor(client, auth_headers, name="1-qavat", floor_number=1)
    floor2 = create_floor(client, auth_headers, name="2-qavat", floor_number=2)
    waypoint = create_waypoint(client, auth_headers, floor_id=floor1["id"], waypoint_id="wp-2")

    response = client.post(
        "/api/kiosks/",
        json={"name": "Mismatch", "floor_id": floor2["id"], "waypoint_id": waypoint["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 400
