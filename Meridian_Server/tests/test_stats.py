from datetime import date, timedelta


def _register(client, email="a@b.com", password="password123", name="Alice Smith"):
    return client.post(
        "/auth/register", json={"email": email, "password": password, "name": name}
    )


def _auth(client, **kw):
    return {"Authorization": f"Bearer {_register(client, **kw).json()['access_token']}"}


def test_stats_open_shipped_velocity(client):
    h = _auth(client)
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h)
    for _ in range(3):
        client.post("/projects/MRD/tasks", json={"title": "x"}, headers=h)
    t = client.post(
        "/projects/MRD/tasks", json={"title": "shipped immediately", "status": "shipped"}, headers=h
    ).json()

    r = client.get("/projects/MRD/stats", headers=h).json()
    assert r["open"] == 3
    assert r["shipped"] == 1
    assert r["velocity"] == 1  # completed_at set on creation
    assert r["overdue"] == 0
    assert t["completed_at"] is not None


def test_stats_overdue_excludes_shipped(client):
    h = _auth(client)
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post(
        "/projects/MRD/tasks",
        json={"title": "late", "due_date": yesterday},
        headers=h,
    )
    client.post(
        "/projects/MRD/tasks",
        json={"title": "late-but-shipped", "due_date": yesterday, "status": "shipped"},
        headers=h,
    )
    r = client.get("/projects/MRD/stats", headers=h).json()
    assert r["overdue"] == 1


def test_stats_requires_auth(client):
    assert client.get("/projects/MRD/stats").status_code == 401


def test_stats_missing_project_404(client):
    h = _auth(client)
    assert client.get("/projects/NOPE/stats", headers=h).status_code == 404
