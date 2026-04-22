def _register(client, email, name):
    return client.post(
        "/auth/register", json={"email": email, "password": "password123", "name": name}
    )


def _auth(client, email, name):
    return {"Authorization": f"Bearer {_register(client, email, name).json()['access_token']}"}


def test_workload_lists_project_members_with_load(client):
    ha = _auth(client, "a@b.com", "Sadie Okafor")
    client.post("/projects", json={"code": "MRD", "name": "Meridian"}, headers=ha)
    me = client.get("/auth/me", headers=ha).json()

    # 3 active tasks assigned to the lead → 30% of the cap (10).
    for _ in range(3):
        client.post(
            "/projects/MRD/tasks",
            json={"title": "task", "assignee_id": me["id"]},
            headers=ha,
        )
    # A shipped task must NOT count toward active load.
    client.post(
        "/projects/MRD/tasks",
        json={"title": "done", "status": "shipped", "assignee_id": me["id"]},
        headers=ha,
    )

    r = client.get("/projects/MRD/workload", headers=ha)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["user_id"] == me["id"]
    assert row["initials"] == "SO"
    assert row["active_tasks"] == 3
    assert row["load_pct"] == 30


def test_workload_requires_auth(client):
    assert client.get("/projects/MRD/workload").status_code == 401
