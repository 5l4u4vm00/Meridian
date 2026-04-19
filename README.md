# Meridian

Meridian is a project management platform where teams track work, visualize progress, and stay aligned. Role-based access, live dashboards, and smart search — all in one clean workspace.

## Stack

Three-tier template:

- **`Meridian_Client/`** — React + Vite frontend (port 8080)
- **`Meridian_Server/`** — FastAPI backend (port 8000)
- **Postgres 16** — database (port 5432)

## Run the full stack

```bash
cp .env.example .env
docker compose up --build
```

- Client: http://localhost:8080
- API: http://localhost:8000 (docs at `/docs`)
- DB health: http://localhost:8000/health/db