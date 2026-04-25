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


def _make_task(client, headers, code="MRD", title="A"):
    r = client.post(f"/projects/{code}/tasks", json={"title": title}, headers=headers)
    assert r.status_code == 201
    return r.json()


def test_create_comment_returns_body_and_initials(client):
    h = _auth(client, name="Sadie Okafor")
    _make_project(client, h)
    t = _make_task(client, h)
    r = client.post(
        f"/tasks/{t['id']}/comments",
        json={"body": "Looks great"},
        headers=h,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["body"] == "Looks great"
    assert body["author_initials"] == "SO"
    assert body["author_name"] == "Sadie Okafor"


def test_list_comments_ordered_by_created_at(client):
    h = _auth(client)
    _make_project(client, h)
    t = _make_task(client, h)
    for body in ("first", "second", "third"):
        client.post(f"/tasks/{t['id']}/comments", json={"body": body}, headers=h)
    rows = client.get(f"/tasks/{t['id']}/comments", headers=h).json()
    assert [c["body"] for c in rows] == ["first", "second", "third"]


def test_comment_routes_require_auth(client):
    r = client.get("/tasks/1/comments")
    assert r.status_code == 401
    r = client.post("/tasks/1/comments", json={"body": "x"})
    assert r.status_code == 401


def test_comment_unknown_task_404(client):
    h = _auth(client)
    r = client.post("/tasks/9999/comments", json={"body": "x"}, headers=h)
    assert r.status_code == 404


def test_comment_emits_activity_and_increments_count(client):
    h = _auth(client)
    _make_project(client, h)
    t = _make_task(client, h)
    client.post(f"/tasks/{t['id']}/comments", json={"body": "hello world"}, headers=h)

    activity = client.get("/projects/MRD/activity", headers=h).json()
    verbs = [e["verb"] for e in activity]
    assert "commented" in verbs

    board = client.get("/projects/MRD/tasks", headers=h).json()
    flat = [tt for col in board["columns"] for tt in col["tasks"]]
    target = next(tt for tt in flat if tt["id"] == t["id"])
    assert target["comment_count"] == 1
    assert target["attachment_count"] == 0


def test_task_detail_endpoint(client):
    h = _auth(client)
    _make_project(client, h)
    t = _make_task(client, h)
    client.post(f"/tasks/{t['id']}/comments", json={"body": "a"}, headers=h)
    r = client.get(f"/tasks/{t['id']}/detail", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["task"]["id"] == t["id"]
    assert len(body["comments"]) == 1
    assert body["attachments"] == []
