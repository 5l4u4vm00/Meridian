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


def test_add_project_member(client):
    headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=headers)
    other = client.post(
        "/auth/register",
        json={"email": "bob@b.com", "password": "password123", "name": "Bob"},
    ).json()
    bob_id = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {other['access_token']}"},
    ).json()["id"]

    r = client.post(
        "/projects/MRD/members",
        json={"user_id": bob_id},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"] == bob_id
    assert body["role"] == "member"

    members = client.get("/projects/MRD/members", headers=headers).json()
    assert {m["email"] for m in members} == {"a@b.com", "bob@b.com"}


def test_add_project_member_idempotent(client):
    headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=headers)
    other = client.post(
        "/auth/register",
        json={"email": "bob@b.com", "password": "password123", "name": "Bob"},
    ).json()
    bob_id = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {other['access_token']}"},
    ).json()["id"]

    r1 = client.post(
        "/projects/MRD/members", json={"user_id": bob_id}, headers=headers
    )
    r2 = client.post(
        "/projects/MRD/members", json={"user_id": bob_id}, headers=headers
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    members = client.get("/projects/MRD/members", headers=headers).json()
    assert len([m for m in members if m["id"] == bob_id]) == 1


def _register_and_get_id(client, email, name="User"):
    tokens = client.post(
        "/auth/register",
        json={"email": email, "password": "password123", "name": name},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = client.get("/auth/me", headers=headers).json()
    return me["id"], headers


def test_change_leader_swaps_member_roles(client):
    lead_headers = _auth_headers(client)  # alice — initial lead
    client.post(
        "/projects", json={"code": "MRD", "name": "x"}, headers=lead_headers
    )
    bob_id, bob_headers = _register_and_get_id(client, "bob@b.com", name="Bob")
    client.post(
        "/projects/MRD/members", json={"user_id": bob_id}, headers=lead_headers
    )

    r = client.patch(
        "/projects/MRD", json={"lead_id": bob_id}, headers=lead_headers
    )
    assert r.status_code == 200, r.text

    members = {
        m["email"]: m["role"]
        for m in client.get("/projects/MRD/members", headers=bob_headers).json()
    }
    assert members == {"a@b.com": "member", "bob@b.com": "lead"}

    # New leader can manage the project
    r2 = client.patch(
        "/projects/MRD", json={"name": "Renamed"}, headers=bob_headers
    )
    assert r2.status_code == 200

    # Old leader is now demoted and can't manage
    r3 = client.patch(
        "/projects/MRD", json={"name": "Nope"}, headers=lead_headers
    )
    assert r3.status_code == 403


def test_change_leader_to_non_member_rejected(client):
    lead_headers = _auth_headers(client)
    client.post(
        "/projects", json={"code": "MRD", "name": "x"}, headers=lead_headers
    )
    bob_id, _ = _register_and_get_id(client, "bob@b.com", name="Bob")

    r = client.patch(
        "/projects/MRD", json={"lead_id": bob_id}, headers=lead_headers
    )
    assert r.status_code == 400


def test_change_leader_unknown_user_rejected(client):
    lead_headers = _auth_headers(client)
    client.post(
        "/projects", json={"code": "MRD", "name": "x"}, headers=lead_headers
    )
    r = client.patch(
        "/projects/MRD", json={"lead_id": 999999}, headers=lead_headers
    )
    assert r.status_code == 404


def test_add_project_member_unknown_user(client):
    headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=headers)
    r = client.post(
        "/projects/MRD/members", json={"user_id": 9999}, headers=headers
    )
    assert r.status_code == 404


def _register_admin(client, email="admin@b.com", name="Admin"):
    """Register a user and promote them to the global admin role."""
    from app.api.deps import get_db
    from app.main import app
    from app.repositories import role_repository, user_repository

    tokens = client.post(
        "/auth/register",
        json={"email": email, "password": "password123", "name": name},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        user = user_repository.get_by_email(db, email)
        role_repository.assign_role(db, user, "admin")
    finally:
        db.close()
    return headers


def test_admin_can_update_non_member_project(client):
    lead_headers = _auth_headers(client)
    client.post(
        "/projects",
        json={"code": "MRD", "name": "x", "color": "#000000"},
        headers=lead_headers,
    )
    admin_headers = _register_admin(client)

    r = client.patch(
        "/projects/MRD",
        json={"name": "Renamed", "color": "#abcdef", "deadline": "2030-01-01"},
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Renamed"
    assert body["color"] == "#abcdef"


def test_admin_can_change_lead_on_non_member_project(client):
    lead_headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=lead_headers)
    bob_id, _ = _register_and_get_id(client, "bob@b.com", name="Bob")
    client.post(
        "/projects/MRD/members", json={"user_id": bob_id}, headers=lead_headers
    )
    admin_headers = _register_admin(client)

    r = client.patch(
        "/projects/MRD", json={"lead_id": bob_id}, headers=admin_headers
    )
    assert r.status_code == 200, r.text
    members = {
        m["email"]: m["role"]
        for m in client.get("/projects/MRD/members", headers=admin_headers).json()
    }
    assert members == {"a@b.com": "member", "bob@b.com": "lead"}


def test_admin_can_delete_non_member_project(client):
    lead_headers = _auth_headers(client)
    client.post("/projects", json={"code": "DEL", "name": "x"}, headers=lead_headers)
    admin_headers = _register_admin(client)

    r = client.delete("/projects/DEL", headers=admin_headers)
    assert r.status_code == 204
    assert client.get("/projects/DEL", headers=lead_headers).status_code == 404


def test_admin_can_list_and_add_members_on_non_member_project(client):
    lead_headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=lead_headers)
    bob_id, _ = _register_and_get_id(client, "bob@b.com", name="Bob")
    admin_headers = _register_admin(client)

    listing = client.get("/projects/MRD/members", headers=admin_headers)
    assert listing.status_code == 200
    assert {m["email"] for m in listing.json()} == {"a@b.com"}

    add = client.post(
        "/projects/MRD/members", json={"user_id": bob_id}, headers=admin_headers
    )
    assert add.status_code == 201, add.text


def test_admin_sees_all_projects_in_listing(client):
    lead_headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=lead_headers)
    client.post("/projects", json={"code": "ATL", "name": "y"}, headers=lead_headers)
    admin_headers = _register_admin(client)

    rows = client.get("/projects", headers=admin_headers).json()
    assert {p["code"] for p in rows} == {"MRD", "ATL"}


def test_non_member_non_admin_blocked(client):
    lead_headers = _auth_headers(client)
    client.post("/projects", json={"code": "MRD", "name": "x"}, headers=lead_headers)
    _, outsider_headers = _register_and_get_id(client, "out@b.com", name="Out")

    assert client.get("/projects/MRD", headers=outsider_headers).status_code == 404
    assert (
        client.patch(
            "/projects/MRD", json={"name": "z"}, headers=outsider_headers
        ).status_code
        == 404
    )
    assert (
        client.delete("/projects/MRD", headers=outsider_headers).status_code == 404
    )
