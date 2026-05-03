"""Authorization matrix: project membership, lead-only actions, admin bypass."""

from app.api.deps import get_db
from app.main import app
from app.repositories import role_repository, user_repository


def _register(client, email, name="User"):
    r = client.post(
        "/auth/register",
        json={"email": email, "password": "password123", "name": name},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _me(client, token):
    return client.get("/auth/me", headers=_headers(token)).json()


def _make_admin(client, email):
    """Promote a user to the global admin role using the live test DB session."""
    db_factory = app.dependency_overrides[get_db]
    gen = db_factory()
    db = next(gen)
    try:
        user = user_repository.get_by_email(db, email)
        assert user is not None
        role_repository.assign_role(db, user, "admin")
    finally:
        gen.close()


# ---------- visibility ----------


def test_non_member_cannot_see_project(client):
    h_a = _headers(_register(client, "a@x.co"))
    h_b = _headers(_register(client, "b@x.co"))
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)

    # B is not a member.
    assert client.get("/projects/MRD", headers=h_b).status_code == 404
    assert client.get("/projects/MRD/members", headers=h_b).status_code == 404
    assert client.get("/projects/MRD/stats", headers=h_b).status_code == 404
    assert client.get("/projects/MRD/workload", headers=h_b).status_code == 404
    assert client.get("/projects/MRD/activity", headers=h_b).status_code == 404
    assert client.get("/projects/MRD/tasks", headers=h_b).status_code == 404


def test_list_projects_filtered_to_membership(client):
    h_a = _headers(_register(client, "a@x.co"))
    h_b = _headers(_register(client, "b@x.co"))
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)
    client.post("/projects", json={"code": "ATL", "name": "Atlas"}, headers=h_b)

    a_codes = {p["code"] for p in client.get("/projects", headers=h_a).json()}
    b_codes = {p["code"] for p in client.get("/projects", headers=h_b).json()}
    assert a_codes == {"MRD"}
    assert b_codes == {"ATL"}


# ---------- lead-only actions ----------


def test_member_cannot_mutate_project_or_manage_members(client):
    h_a = _headers(_register(client, "a@x.co"))
    h_b_token = _register(client, "b@x.co")
    bob_id = _me(client, h_b_token)["id"]
    h_b = _headers(h_b_token)
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)
    # A (lead) adds B as plain member.
    r = client.post(
        "/projects/MRD/members",
        json={"user_id": bob_id, "role": "member"},
        headers=h_a,
    )
    assert r.status_code == 201

    # B can read but not mutate.
    assert client.get("/projects/MRD", headers=h_b).status_code == 200
    assert (
        client.patch("/projects/MRD", json={"name": "x"}, headers=h_b).status_code
        == 403
    )
    assert client.delete("/projects/MRD", headers=h_b).status_code == 403
    other_token = _register(client, "c@x.co")
    other_id = _me(client, other_token)["id"]
    assert (
        client.post(
            "/projects/MRD/members",
            json={"user_id": other_id},
            headers=h_b,
        ).status_code
        == 403
    )


def test_lead_can_mutate_project(client):
    h_a = _headers(_register(client, "a@x.co"))
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)
    assert (
        client.patch(
            "/projects/MRD", json={"name": "Renamed"}, headers=h_a
        ).status_code
        == 200
    )
    assert client.delete("/projects/MRD", headers=h_a).status_code == 204


# ---------- members can CRUD tasks, comments ----------


def test_member_can_crud_tasks_and_comments(client):
    h_a = _headers(_register(client, "a@x.co"))
    h_b_token = _register(client, "b@x.co")
    bob_id = _me(client, h_b_token)["id"]
    h_b = _headers(h_b_token)
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)
    client.post(
        "/projects/MRD/members", json={"user_id": bob_id}, headers=h_a
    )

    t = client.post(
        "/projects/MRD/tasks", json={"title": "by bob"}, headers=h_b
    )
    assert t.status_code == 201
    tid = t.json()["id"]
    assert (
        client.patch(
            f"/tasks/{tid}", json={"title": "renamed by bob"}, headers=h_b
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/tasks/{tid}/comments", json={"body": "hi"}, headers=h_b
        ).status_code
        == 201
    )


def test_non_member_cannot_touch_tasks(client):
    h_a = _headers(_register(client, "a@x.co"))
    h_b = _headers(_register(client, "b@x.co"))
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)
    t = client.post(
        "/projects/MRD/tasks", json={"title": "secret"}, headers=h_a
    ).json()

    assert client.get(f"/tasks/{t['id']}", headers=h_b).status_code == 404
    assert (
        client.patch(
            f"/tasks/{t['id']}", json={"title": "x"}, headers=h_b
        ).status_code
        == 404
    )
    assert client.delete(f"/tasks/{t['id']}", headers=h_b).status_code == 404
    assert (
        client.get(f"/tasks/{t['id']}/comments", headers=h_b).status_code == 404
    )
    assert (
        client.post(
            f"/tasks/{t['id']}/comments", json={"body": "x"}, headers=h_b
        ).status_code
        == 404
    )
    assert (
        client.get(f"/tasks/{t['id']}/attachments", headers=h_b).status_code == 404
    )


# ---------- admin bypass ----------


def test_admin_can_access_any_project(client):
    h_a = _headers(_register(client, "a@x.co"))
    admin_token = _register(client, "admin@x.co")
    _make_admin(client, "admin@x.co")
    h_admin = _headers(admin_token)

    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)

    # Admin sees all projects in list, even without membership.
    codes = {p["code"] for p in client.get("/projects", headers=h_admin).json()}
    assert "MRD" in codes

    # Read & mutate any project.
    assert client.get("/projects/MRD", headers=h_admin).status_code == 200
    assert (
        client.patch(
            "/projects/MRD", json={"name": "Admin renamed"}, headers=h_admin
        ).status_code
        == 200
    )
    # Admin can manage members.
    other_token = _register(client, "c@x.co")
    other_id = _me(client, other_token)["id"]
    assert (
        client.post(
            "/projects/MRD/members",
            json={"user_id": other_id, "role": "member"},
            headers=h_admin,
        ).status_code
        == 201
    )
    # Admin can create + delete tasks in a project they don't belong to.
    t = client.post(
        "/projects/MRD/tasks", json={"title": "from admin"}, headers=h_admin
    )
    assert t.status_code == 201
    assert client.delete(f"/tasks/{t.json()['id']}", headers=h_admin).status_code == 204


# ---------- regression: add_member honors role ----------


def test_add_member_honors_lead_role(client):
    h_a = _headers(_register(client, "a@x.co"))
    bob_token = _register(client, "b@x.co")
    bob_id = _me(client, bob_token)["id"]
    h_b = _headers(bob_token)
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)
    r = client.post(
        "/projects/MRD/members",
        json={"user_id": bob_id, "role": "lead"},
        headers=h_a,
    )
    assert r.status_code == 201, r.text
    assert r.json()["role"] == "lead"
    # Bob is now a lead and can mutate the project.
    assert (
        client.patch(
            "/projects/MRD", json={"name": "by bob"}, headers=h_b
        ).status_code
        == 200
    )


def test_add_member_rejects_unknown_role(client):
    h_a = _headers(_register(client, "a@x.co"))
    bob_id = _me(client, _register(client, "b@x.co"))["id"]
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=h_a)
    r = client.post(
        "/projects/MRD/members",
        json={"user_id": bob_id, "role": "owner"},
        headers=h_a,
    )
    assert r.status_code == 422
