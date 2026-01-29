def test_create_floor_valid(client, auth_headers):
    response = client.post(
        "/api/floors/",
        json={"name": "3-qavat", "floor_number": 3},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "3-qavat"
    assert data["floor_number"] == 3
    assert "id" in data

def test_get_floors(client, auth_headers):
    # Create one floor
    client.post(
        "/api/floors/",
        json={"name": "List Test", "floor_number": 10},
        headers=auth_headers
    )
    
    response = client.get("/api/floors/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_floor_by_id(client, auth_headers):
    create_resp = client.post(
        "/api/floors/",
        json={"name": "Get ID Test", "floor_number": 11},
        headers=auth_headers
    )
    floor_id = create_resp.json()["id"]
    
    response = client.get(f"/api/floors/{floor_id}")
    assert response.status_code == 200
    assert response.json()["id"] == floor_id

def test_update_floor(client, auth_headers):
    create_resp = client.post(
        "/api/floors/",
        json={"name": "Update Test", "floor_number": 12},
        headers=auth_headers
    )
    floor_id = create_resp.json()["id"]
    
    response = client.put(
        f"/api/floors/{floor_id}",
        json={"name": "Updated Name", "floor_number": 12},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

def test_delete_floor(client, auth_headers):
    create_resp = client.post(
        "/api/floors/",
        json={"name": "Delete Test", "floor_number": 13},
        headers=auth_headers
    )
    floor_id = create_resp.json()["id"]
    
    response = client.delete(f"/api/floors/{floor_id}", headers=auth_headers)
    assert response.status_code == 200
    
    get_resp = client.get(f"/api/floors/{floor_id}")
    assert get_resp.status_code == 404
