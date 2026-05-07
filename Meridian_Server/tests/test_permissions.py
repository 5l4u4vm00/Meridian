from fastapi import Depends

from app.api.deps import get_db, require_permission, require_role
from app.core.security import decode_token
from app.main import app
from app.repositories import role_repository, user_repository


def _register_test_routes() -> None:
    if getattr(app.state, "_perm_test_routes_registered", False):
        return

    @app.get("/_test/needs-perm")
    def needs_perm(_=Depends(require_permission("widget:write"))):
        return {"ok": True}

    @app.get("/_test/needs-admin")
    def needs_admin(_=Depends(require_role("admin"))):
        return {"ok": True}

    app.state._perm_test_routes_registered = True


_register_test_routes()


def _register(client, email="a@b.com", password="password123", name="Alice"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": name},
    )


def _db_from_client(client):
    override = client.app.dependency_overrides[get_db]
    return next(override())


def test_new_user_gets_default_role(client):
    tokens = _register(client).json()
    claims = decode_token(tokens["access_token"])
    assert claims.get("role") == "user"
    assert set(claims.get("perms", [])) >= {"users:read", "content:read"}

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    body = me.json()
    assert body["role"] == "user"
    assert set(body["permissions"]) >= {"users:read", "content:read"}


def test_role_assignment_reflected_in_jwt_and_me(client):
    _register(client)
    db = _db_from_client(client)
    try:
        role_repository.ensure_role(db, "admin", ["widget:write", "widget:read"])
        user = user_repository.get_by_email(db, "a@b.com")
        role_repository.assign_role(db, user, "admin")
    finally:
        db.close()

    login = client.post("/auth/login", json={"email": "a@b.com", "password": "password123"})
    assert login.status_code == 200
    tokens = login.json()
    claims = decode_token(tokens["access_token"])
    assert claims["role"] == "admin"
    assert {"widget:write", "widget:read"} <= set(claims["perms"])

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    body = me.json()
    assert body["role"] == "admin"
    assert {"widget:write", "widget:read"} <= set(body["permissions"])


def test_require_permission_forbids_without_perm(client):
    tokens = _register(client).json()
    r = client.get(
        "/_test/needs-perm",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 403


def test_require_permission_allows_with_perm(client):
    _register(client)
    db = _db_from_client(client)
    try:
        role_repository.ensure_role(db, "writer", ["widget:write"])
        user = user_repository.get_by_email(db, "a@b.com")
        role_repository.assign_role(db, user, "writer")
    finally:
        db.close()

    tokens = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "password123"}
    ).json()
    r = client.get(
        "/_test/needs-perm",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 200


def test_require_role_checks_role_claim(client):
    _register(client)
    db = _db_from_client(client)
    try:
        role_repository.ensure_role(db, "admin", [])
        role_repository.ensure_role(db, "member", [])
        user = user_repository.get_by_email(db, "a@b.com")
        role_repository.assign_role(db, user, "member")
    finally:
        db.close()

    tokens = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "password123"}
    ).json()
    denied = client.get(
        "/_test/needs-admin",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert denied.status_code == 403

    db = _db_from_client(client)
    try:
        user = user_repository.get_by_email(db, "a@b.com")
        role_repository.assign_role(db, user, "admin")
    finally:
        db.close()

    tokens = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "password123"}
    ).json()
    allowed = client.get(
        "/_test/needs-admin",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert allowed.status_code == 200


def test_require_permission_rejects_missing_token(client):
    r = client.get("/_test/needs-perm")
    assert r.status_code == 401


def test_seed_does_not_create_retired_editor_role(client):
    db = _db_from_client(client)
    try:
        assert role_repository.get_role_by_name(db, "editor") is None
        assert role_repository.get_role_by_name(db, "admin") is not None
        assert role_repository.get_role_by_name(db, "user") is not None
    finally:
        db.close()


def test_set_user_role_gated_by_users_manage_permission(client):
    """Non-admin user with users:manage permission can set roles."""
    _register(client, email="manager@example.com")
    _register(client, email="target@example.com")
    db = _db_from_client(client)
    try:
        role_repository.ensure_role(db, "user_manager", ["users:manage"])
        manager = user_repository.get_by_email(db, "manager@example.com")
        role_repository.assign_role(db, manager, "user_manager")
        target_id = user_repository.get_by_email(db, "target@example.com").id
    finally:
        db.close()

    tokens = client.post(
        "/auth/login", json={"email": "manager@example.com", "password": "password123"}
    ).json()
    r = client.put(
        f"/users/{target_id}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 200
