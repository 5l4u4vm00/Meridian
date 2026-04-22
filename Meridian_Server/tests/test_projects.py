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
