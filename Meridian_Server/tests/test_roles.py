from app.api.deps import get_db
from app.core.security import decode_token
from app.repositories import role_repository, user_repository


def _register(client, email, name="User"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": "password123", "name": name},
    ).json()


def _login(client, email):
    return client.post(
        "/auth/login", json={"email": email, "password": "password123"}
    ).json()


def _db(client):
    return next(client.app.dependency_overrides[get_db]())


def _promote_to_admin(client, email):
    db = _db(client)
    try:
        user = user_repository.get_by_email(db, email)
        role_repository.assign_role(db, user, "admin")
    finally:
        db.close()


def test_non_admin_cannot_assign_role(client):
    _register(client, "alice@example.com")
    admin_tokens = _register(client, "bob@example.com")

    alice_id = user_repository.get_by_email(_db(client), "alice@example.com").id
    r = client.put(
        f"/users/{alice_id}/role",
        json={"role": "editor"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert r.status_code == 403


def test_admin_can_promote_user_to_editor(client):
    _register(client, "alice@example.com")
    _register(client, "admin@example.com")
    _promote_to_admin(client, "admin@example.com")
    admin_tokens = _login(client, "admin@example.com")

    alice_id = user_repository.get_by_email(_db(client), "alice@example.com").id
    r = client.put(
        f"/users/{alice_id}/role",
        json={"role": "editor"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "editor"

    alice_tokens = _login(client, "alice@example.com")
    claims = decode_token(alice_tokens["access_token"])
    assert claims["role"] == "editor"
    assert "content:write" in claims["perms"]


def test_admin_rejects_unknown_role(client):
    _register(client, "admin@example.com")
    _promote_to_admin(client, "admin@example.com")
    admin_tokens = _login(client, "admin@example.com")

    admin_id = user_repository.get_by_email(_db(client), "admin@example.com").id
    r = client.put(
        f"/users/{admin_id}/role",
        json={"role": "ghost"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert r.status_code == 400


def test_admin_role_assignment_on_missing_user(client):
    _register(client, "admin@example.com")
    _promote_to_admin(client, "admin@example.com")
    admin_tokens = _login(client, "admin@example.com")

    r = client.put(
        "/users/9999/role",
        json={"role": "editor"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert r.status_code == 404
