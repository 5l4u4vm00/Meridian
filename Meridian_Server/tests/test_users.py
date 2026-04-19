def test_create_and_get_user(client):
    resp = client.post("/users", json={"email": "a@b.com", "name": "Ada"})
    assert resp.status_code == 201
    created = resp.json()
    assert created["email"] == "a@b.com"
    assert created["name"] == "Ada"
    user_id = created["id"]

    resp = client.get(f"/users/{user_id}")
    assert resp.status_code == 200
    assert resp.json() == created


def test_get_missing_user(client):
    resp = client.get("/users/999")
    assert resp.status_code == 404


def test_list_users(client):
    client.post("/users", json={"email": "x@y.com", "name": "X"})
    client.post("/users", json={"email": "y@z.com", "name": "Y"})
    resp = client.get("/users")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
