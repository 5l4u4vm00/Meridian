def _register(client, email="a@b.com", password="password123", name="Alice Smith"):
    return client.post(
        "/auth/register", json={"email": email, "password": password, "name": name}
    )


def _auth(client):
    return {"Authorization": f"Bearer {_register(client).json()['access_token']}"}


def test_activity_records_create_and_move(client):
    h = _auth(client)
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h)
    t = client.post("/projects/MRD/tasks", json={"title": "A"}, headers=h).json()
    client.post(f"/tasks/{t['id']}/move", json={"status": "in_progress"}, headers=h)

    events = client.get("/projects/MRD/activity", headers=h).json()
    # Newest first: moved, then created.
    verbs = [e["verb"] for e in events]
    assert verbs[:2] == ["moved", "created"]
    move_event = events[0]
    assert move_event["meta"] == {"from": "backlog", "to": "in_progress"}
    assert move_event["task_code"] == "MRD-1"
    assert move_event["actor_initials"] == "AS"


def test_activity_ship_emits_completed(client):
    h = _auth(client)
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h)
    t = client.post("/projects/MRD/tasks", json={"title": "A"}, headers=h).json()
    client.post(f"/tasks/{t['id']}/move", json={"status": "shipped"}, headers=h)

    events = client.get("/projects/MRD/activity", headers=h).json()
    verbs = [e["verb"] for e in events]
    assert "completed" in verbs
    assert "moved" in verbs


def test_activity_update_event(client):
    h = _auth(client)
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h)
    t = client.post("/projects/MRD/tasks", json={"title": "A"}, headers=h).json()
    client.patch(f"/tasks/{t['id']}", json={"priority": "high"}, headers=h)

    events = client.get("/projects/MRD/activity", headers=h).json()
    top = events[0]
    assert top["verb"] == "updated"
    assert top["meta"] == {"fields": ["priority"]}


def test_activity_requires_auth(client):
    assert client.get("/projects/MRD/activity").status_code == 401
