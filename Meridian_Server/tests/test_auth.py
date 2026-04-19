from datetime import datetime, timedelta, timezone

import pytest

from app.core import security
from app.models.refresh_token import RefreshToken


def _register(client, email="a@b.com", password="password123", name="Alice"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": name},
    )


def test_register_returns_token_pair(client):
    r = _register(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_register_duplicate_email_rejected(client):
    _register(client)
    r = _register(client)
    assert r.status_code == 400


def test_login_success_and_failure(client):
    _register(client)
    ok = client.post("/auth/login", json={"email": "a@b.com", "password": "password123"})
    assert ok.status_code == 200
    bad = client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert bad.status_code == 401
    missing = client.post("/auth/login", json={"email": "nope@b.com", "password": "x"})
    assert missing.status_code == 401


def test_me_requires_valid_bearer(client):
    tokens = _register(client).json()
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"


def test_me_rejects_refresh_token(client):
    tokens = _register(client).json()
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert r.status_code == 401


def test_refresh_issues_new_access_token(client):
    tokens = _register(client).json()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new_access = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200


def test_logout_revokes_refresh(client):
    tokens = _register(client).json()
    assert client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


def test_expired_refresh_rejected(client, monkeypatch):
    tokens = _register(client).json()
    # Force the stored refresh row to be expired.
    from app.api.deps import get_db

    db_gen = app_gen = None
    # pull the overridden session
    override = client.app.dependency_overrides[get_db]
    db = next(override())
    try:
        row = db.query(RefreshToken).first()
        row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


def test_oauth_google_callback_creates_user(client, monkeypatch):
    async def fake_authorize(request):
        return {
            "userinfo": {
                "sub": "google-123",
                "email": "oauth@example.com",
                "name": "OAuth User",
            }
        }

    from app.core.oauth import oauth

    class FakeClient:
        authorize_access_token = staticmethod(fake_authorize)

    # Register a fake google client on the OAuth registry for this test.
    monkeypatch.setattr(oauth, "_clients", {**oauth._clients, "google": FakeClient()}, raising=False)
    # Some Authlib versions expose clients via __getattr__ -> _clients lookup; ensure attribute access works.
    monkeypatch.setattr(
        "app.api.routes.auth._require_client",
        lambda provider: FakeClient() if provider == "google" else (_ for _ in ()).throw(Exception()),
    )

    r = client.get("/auth/google/callback")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"] and body["refresh_token"]

    # Calling again should link to the same user (no duplicate).
    r2 = client.get("/auth/google/callback")
    assert r2.status_code == 200
    tokens = r2.json()
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "oauth@example.com"
