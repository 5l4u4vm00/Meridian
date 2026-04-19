# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Stack

Three-tier app in one repo:

- `Meridian_Client/` — React 19 + Vite frontend (port 8080)
- `Meridian_Server/` — FastAPI + SQLAlchemy backend (port 8000)
- Postgres 16 via `docker-compose.yml` (port 5432)

## Common commands

Full stack (from repo root):

```bash
cp .env.example .env
docker compose up --build
```

Backend (from `Meridian_Server/`):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload       # dev server on :8000, Swagger at /docs
pytest                              # full test suite
pytest tests/test_users.py::test_name  # single test
```

Frontend (from `Meridian_Client/`):

```bash
npm install
npm run dev       # Vite dev server
npm run build
npm run lint
```

## Backend architecture

Strict layered flow: `routes → services → repositories → DB`.

- `app/api/routes/` — FastAPI routers, one module per resource. Routes handle HTTP only (request parsing, status codes, `HTTPException`). Never import SQLAlchemy here.
- `app/services/` — business logic / use cases. Must not import `fastapi`. Called by routes with a `Session` injected via `Depends(get_db)`.
- `app/repositories/` — SQLAlchemy queries. Only layer that touches the ORM directly.
- `app/models/` — SQLAlchemy ORM tables (register with `Base` by importing them in `app/__init__.py` / `app/main.py` so `create_all` sees them).
- `app/schemas/` — Pydantic request/response models. Keep separate from ORM models.
- `app/core/config.py` — `pydantic-settings`; reads `DATABASE_URL` from env or `.env`.
- `app/core/db.py` — engine, `SessionLocal`, `Base`.
- `app/api/deps.py` — `get_db()` dependency (yields a session, closes on teardown).

On startup `app/main.py` calls `Base.metadata.create_all(bind=engine)`. This is dev scaffolding — swap in Alembic before real data lands. Adding a new model requires ensuring its module is imported so the table is registered.

Tests (`Meridian_Server/tests/`) use `TestClient` against an in-memory SQLite engine and override `get_db` via `app.dependency_overrides` (see `tests/conftest.py`). When adding a route, follow the existing pattern of testing through the client rather than unit-testing services in isolation.

## Frontend

Standard Vite + React template with ESLint flat config (`eslint.config.js`). No TypeScript, no routing/state libraries wired up yet.

## Docker / env

`docker-compose.yml` builds `server` from `Meridian_Server/Dockerfile` and `client` from `Meridian_Client/Dockerfile`, and wires `DATABASE_URL` to the `db` service. The compose file uses `POSTGRES_USER/PASSWORD/DB` from `.env` (see `.env.example`). Server waits on a Postgres healthcheck before starting.