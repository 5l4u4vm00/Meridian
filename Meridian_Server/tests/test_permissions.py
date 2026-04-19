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


def test_new_user_has_no_role_or_perms(client):
    tokens = _register(client).json()
    claims = decode_token(tokens["access_token"])
    assert "role" not in claims
    assert claims.get("perms", []) == []

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    body = me.json()
    assert body["role"] is None
    assert body["permissions"] == []


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
    assert set(claims["perms"]) == {"widget:write", "widget:read"}

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    body = me.json()
    assert body["role"] == "admin"
    assert set(body["permissions"]) == {"widget:write", "widget:read"}


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
        role_repository.ensure_role(db, "editor", ["widget:write"])
        user = user_repository.get_by_email(db, "a@b.com")
        role_repository.assign_role(db, user, "editor")
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
