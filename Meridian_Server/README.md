# Meridian Server

FastAPI backend for Meridian, organized in a three-layer architecture.

## Layout

```
app/
  api/           presentation: routers + FastAPI deps
    routes/      one module per resource
  services/      business logic / use cases
  repositories/  data access (SQLAlchemy queries)
  models/        SQLAlchemy ORM models (tables)
  schemas/       Pydantic request/response models
  core/          config, db engine, Base
  main.py        app factory, router mounting
tests/           pytest + TestClient against in-memory SQLite
```

Request flow: `routes → services → repositories → DB`.
Routes never touch SQLAlchemy; services never touch FastAPI.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

App runs at http://localhost:8000 (Swagger UI at `/docs`).

## Tests

```bash
pytest
```

## Docker

```bash
docker build -t meridian-server .
docker run --rm -p 8000:8000 meridian-server
```

## Notes

- `Base.metadata.create_all()` runs on startup for scaffolding. Swap in Alembic before any real data lands.
- Config via `pydantic-settings` reads `DATABASE_URL` from env or `.env`.
