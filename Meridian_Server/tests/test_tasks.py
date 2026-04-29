def _register(client, email="a@b.com", password="password123", name="Alice Smith"):
    return client.post(
        "/auth/register", json={"email": email, "password": password, "name": name}
    )


def _auth(client, email="a@b.com", name="Alice Smith"):
    tokens = _register(client, email=email, name=name).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _make_project(client, headers, code="MRD", name="Meridian Rebrand"):
    r = client.post("/projects", json={"code": code, "name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()


def test_create_task_auto_numbers(client):
    h = _auth(client)
    _make_project(client, h)
    t1 = client.post(
        "/projects/MRD/tasks",
        json={"title": "Audit typography"},
        headers=h,
    ).json()
    t2 = client.post(
        "/projects/MRD/tasks",
        json={"title": "Refine wordmark", "priority": "high", "tags": ["identity"]},
        headers=h,
    ).json()
    assert t1["number"] == 1
    assert t2["number"] == 2
    assert t1["code"] == "MRD-1"
    assert t2["code"] == "MRD-2"
    assert t2["priority"] == "high"
    assert t2["tags"] == ["identity"]
    assert t1["assignee_initials"] is None


def test_board_grouped_by_status(client):
    h = _auth(client)
    _make_project(client, h)
    client.post("/projects/MRD/tasks", json={"title": "A"}, headers=h)
    client.post(
        "/projects/MRD/tasks",
        json={"title": "B", "status": "in_progress"},
        headers=h,
    )
    board = client.get("/projects/MRD/tasks", headers=h).json()
    status_map = {c["status"]: [t["title"] for t in c["tasks"]] for c in board["columns"]}
    assert status_map["backlog"] == ["A"]
    assert status_map["in_progress"] == ["B"]
    assert status_map["in_review"] == []
    assert status_map["shipped"] == []


def test_move_task_reorders(client):
    h = _auth(client)
    _make_project(client, h)
    a = client.post("/projects/MRD/tasks", json={"title": "A"}, headers=h).json()
    b = client.post("/projects/MRD/tasks", json={"title": "B"}, headers=h).json()
    c = client.post("/projects/MRD/tasks", json={"title": "C"}, headers=h).json()

    # Move C to top of in_progress column.
    r = client.post(
        f"/tasks/{c['id']}/move",
        json={"status": "in_progress"},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"

    # Move A between C (already in progress) and nothing → after C.
    r = client.post(
        f"/tasks/{a['id']}/move",
        json={"status": "in_progress", "before_task_id": c["id"]},
        headers=h,
    )
    assert r.status_code == 200

    board = client.get("/projects/MRD/tasks", headers=h).json()
    titles = {col["status"]: [t["title"] for t in col["tasks"]] for col in board["columns"]}
    assert titles["backlog"] == ["B"]
    assert titles["in_progress"] == ["C", "A"]


def test_move_to_shipped_sets_completed_at(client):
    h = _auth(client)
    _make_project(client, h)
    t = client.post("/projects/MRD/tasks", json={"title": "A"}, headers=h).json()
    assert t["completed_at"] is None
    r = client.post(
        f"/tasks/{t['id']}/move", json={"status": "shipped"}, headers=h
    ).json()
    assert r["completed_at"] is not None
    # Moving back off shipped clears completed_at.
    r2 = client.post(
        f"/tasks/{t['id']}/move", json={"status": "in_review"}, headers=h
    ).json()
    assert r2["completed_at"] is None


def test_update_task_fields(client):
    h = _auth(client)
    _make_project(client, h)
    t = client.post("/projects/MRD/tasks", json={"title": "A"}, headers=h).json()
    r = client.patch(
        f"/tasks/{t['id']}",
        json={"title": "A-renamed", "priority": "high", "tags": ["x"]},
        headers=h,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "A-renamed"
    assert body["priority"] == "high"
    assert body["tags"] == ["x"]


def test_assignee_initials_populated(client):
    h = _auth(client, email="sadie@folio.co", name="Sadie Okafor")
    _make_project(client, h)
    me = client.get("/auth/me", headers=h).json()
    t = client.post(
        "/projects/MRD/tasks",
        json={"title": "Assigned", "assignee_id": me["id"]},
        headers=h,
    ).json()
    assert t["assignee_initials"] == "SO"


def test_task_routes_require_auth(client):
    r = client.get("/projects/MRD/tasks")
    assert r.status_code == 401


def test_my_tasks_returns_only_assigned_across_projects(client):
    h_a = _auth(client, email="alice@x.co", name="Alice Smith")
    me_a = client.get("/auth/me", headers=h_a).json()
    h_b = _auth(client, email="bob@x.co", name="Bob Jones")
    me_b = client.get("/auth/me", headers=h_b).json()

    _make_project(client, h_a, code="MRD", name="Meridian")
    _make_project(client, h_a, code="ATL", name="Atlas")

    client.post(
        "/projects/MRD/tasks",
        json={"title": "Mine in MRD", "assignee_id": me_a["id"]},
        headers=h_a,
    )
    client.post(
        "/projects/ATL/tasks",
        json={"title": "Mine in ATL", "assignee_id": me_a["id"]},
        headers=h_a,
    )
    client.post(
        "/projects/MRD/tasks",
        json={"title": "Bob's task", "assignee_id": me_b["id"]},
        headers=h_a,
    )
    client.post("/projects/MRD/tasks", json={"title": "Unassigned"}, headers=h_a)

    rows = client.get("/my-tasks", headers=h_a).json()
    titles = sorted(t["title"] for t in rows)
    assert titles == ["Mine in ATL", "Mine in MRD"]
    codes = {t["title"]: t["project_code"] for t in rows}
    assert codes["Mine in MRD"] == "MRD"
    assert codes["Mine in ATL"] == "ATL"
    assert all("project_color" in t and "project_name" in t for t in rows)


def test_my_tasks_excludes_shipped_by_default(client):
    h = _auth(client)
    me = client.get("/auth/me", headers=h).json()
    _make_project(client, h)
    open_t = client.post(
        "/projects/MRD/tasks",
        json={"title": "Open", "assignee_id": me["id"]},
        headers=h,
    ).json()
    shipped_t = client.post(
        "/projects/MRD/tasks",
        json={"title": "Done", "assignee_id": me["id"]},
        headers=h,
    ).json()
    client.post(
        f"/tasks/{shipped_t['id']}/move", json={"status": "shipped"}, headers=h
    )

    default = client.get("/my-tasks", headers=h).json()
    assert [t["title"] for t in default] == ["Open"]
    assert default[0]["id"] == open_t["id"]

    incl = client.get("/my-tasks?include_shipped=true", headers=h).json()
    assert sorted(t["title"] for t in incl) == ["Done", "Open"]


def test_my_tasks_empty_when_nothing_assigned(client):
    h = _auth(client)
    _make_project(client, h)
    client.post("/projects/MRD/tasks", json={"title": "Unassigned"}, headers=h)
    rows = client.get("/my-tasks", headers=h).json()
    assert rows == []


def test_my_tasks_requires_auth(client):
    assert client.get("/my-tasks").status_code == 401
