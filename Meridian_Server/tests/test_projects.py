def _register(client, email="a@b.com", password="password123", name="Alice"):
    return client.post(
        "/auth/register", json={"email": email, "password": password, "name": name}
    )


def _auth_headers(client):
    tokens = _register(client).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_create_and_list_project(client):
    headers = _auth_headers(client)
    r = client.post(
        "/projects",
        json={"code": "MRD", "name": "Meridian Rebrand", "color": "#c4511c"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["code"] == "MRD"
    assert body["name"] == "Meridian Rebrand"

    lst = client.get("/projects", headers=headers)
    assert lst.status_code == 200
    data = lst.json()
    assert len(data) == 1
    assert data[0]["code"] == "MRD"
    assert data[0]["task_count"] == 0
    assert data[0]["open_count"] == 0
    assert data[0]["shipped_count"] == 0
    assert data[0]["last_activity"] is None


def test_list_project_includes_summary_counts(client):
    headers = _auth_headers(client)
    client.post(
        "/projects",
        json={"code": "MRD", "name": "Meridian"},
        headers=headers,
    )
    t1 = client.post(
        "/projects/MRD/tasks",
        json={"title": "design", "status": "backlog"},
        headers=headers,
    )
    assert t1.status_code == 201, t1.text
    t2 = client.post(
        "/projects/MRD/tasks",
        json={"title": "ship it", "status": "shipped"},
        headers=headers,
    )
    assert t2.status_code == 201, t2.text

    lst = client.get("/projects", headers=headers).json()
    row = next(p for p in lst if p["code"] == "MRD")
    assert row["task_count"] == 2
    assert row["open_count"] == 1
    assert row["shipped_count"] == 1
    assert row["last_activity"] is not None


def test_project_requires_auth(client):
    r = client.get("/projects")
    assert r.status_code == 401
    r2 = client.post("/projects", json={"code": "MRD", "name": "x"})
    assert r2.status_code == 401


def test_duplicate_project_code_rejected(client):
    headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=headers)
    r = client.post("/projects", json={"code": "MRD", "name": "y"}, headers=headers)
    assert r.status_code == 409


def test_get_project_by_code(client):
    headers = _auth_headers(client)
    client.post("/projects", json={"code": "ATL", "name": "Atlas"}, headers=headers)
    r = client.get("/projects/ATL", headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Atlas"

    miss = client.get("/projects/NOPE", headers=headers)
    assert miss.status_code == 404


def test_delete_project_removes_tasks(client):
    headers = _auth_headers(client)
    client.post("/projects", json={"code": "DEL", "name": "Doomed"}, headers=headers)
    client.post(
        "/projects/DEL/tasks",
        json={"title": "wont survive", "status": "backlog"},
        headers=headers,
    )

    r = client.delete("/projects/DEL", headers=headers)
    assert r.status_code == 204

    miss = client.get("/projects/DEL", headers=headers)
    assert miss.status_code == 404
    lst = client.get("/projects", headers=headers).json()
    assert all(p["code"] != "DEL" for p in lst)


def test_delete_project_not_found(client):
    headers = _auth_headers(client)
    r = client.delete("/projects/NOPE", headers=headers)
    assert r.status_code == 404


def test_list_project_members(client):
    headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=headers)
    r = client.get("/projects/MRD/members", headers=headers)
    assert r.status_code == 200
    members = r.json()
    assert len(members) == 1
    assert members[0]["email"] == "a@b.com"
    assert members[0]["role"] == "lead"
