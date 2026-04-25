from app.core.config import settings


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


def _upload(client, task_id, headers, *, name="doc.png", data=b"PNGDATA", mime="image/png"):
    return client.post(
        f"/tasks/{task_id}/attachments",
        files={"file": (name, data, mime)},
        headers=headers,
    )


def test_create_attachment_returns_download_url(client):
    h = _auth(client, name="Sadie Okafor")
    _make_project(client, h)
    t = _make_task(client, h)
    r = _upload(client, t["id"], h, name="spec.pdf", data=b"%PDF-1.4 stub", mime="application/pdf")
    assert r.status_code == 201
    body = r.json()
    assert body["filename"] == "spec.pdf"
    assert body["url"] == f"/attachments/{body['id']}/download"
    assert body["uploader_initials"] == "SO"
    assert body["size_bytes"] == len(b"%PDF-1.4 stub")


def test_attachment_routes_require_auth(client):
    r = client.get("/tasks/1/attachments")
    assert r.status_code == 401
    r = client.post("/tasks/1/attachments", files={"file": ("x.txt", b"x", "text/plain")})
    assert r.status_code == 401
    r = client.get("/attachments/1/download")
    assert r.status_code == 401


def test_attachment_unknown_task_404(client):
    h = _auth(client)
    r = _upload(client, 9999, h)
    assert r.status_code == 404


def test_download_unknown_attachment_404(client):
    h = _auth(client)
    r = client.get("/attachments/9999/download", headers=h)
    assert r.status_code == 404


def test_attachment_round_trip_bytes(client):
    h = _auth(client)
    _make_project(client, h)
    t = _make_task(client, h)
    payload = b"\x89PNG\r\n\x1a\nfake-bytes"
    created = _upload(client, t["id"], h, name="img.png", data=payload, mime="image/png").json()

    r = client.get(created["url"], headers=h)
    assert r.status_code == 200
    assert r.content == payload
    assert r.headers.get("content-type", "").startswith("image/png")
    assert "img.png" in r.headers.get("content-disposition", "")


def test_attachment_emits_activity_and_increments_count(client):
    h = _auth(client)
    _make_project(client, h)
    t = _make_task(client, h)
    _upload(client, t["id"], h, name="doc.png")

    activity = client.get("/projects/MRD/activity", headers=h).json()
    events = [e for e in activity if e["verb"] == "attached"]
    assert len(events) == 1
    assert events[0]["meta"]["filename"] == "doc.png"

    board = client.get("/projects/MRD/tasks", headers=h).json()
    flat = [tt for col in board["columns"] for tt in col["tasks"]]
    target = next(tt for tt in flat if tt["id"] == t["id"])
    assert target["attachment_count"] == 1


def test_list_attachments_ordered(client):
    h = _auth(client)
    _make_project(client, h)
    t = _make_task(client, h)
    for name in ("a.txt", "b.txt", "c.txt"):
        _upload(client, t["id"], h, name=name, data=name.encode(), mime="text/plain")
    rows = client.get(f"/tasks/{t['id']}/attachments", headers=h).json()
    assert [a["filename"] for a in rows] == ["a.txt", "b.txt", "c.txt"]


def test_attachment_size_cap_returns_413(client, monkeypatch):
    monkeypatch.setattr(settings, "attachment_max_bytes", 8)
    h = _auth(client)
    _make_project(client, h)
    t = _make_task(client, h)
    r = _upload(client, t["id"], h, name="big.bin", data=b"123456789", mime="application/octet-stream")
    assert r.status_code == 413
