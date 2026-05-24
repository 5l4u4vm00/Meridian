# Meridian

Meridian is a project management platform where teams track work, visualize progress, and stay aligned. Role-based access, live dashboards, and smart search — all in one clean workspace.

## Features

- Email/password auth with refresh tokens, plus Google and GitHub OAuth sign-in
- Role-based access control with project membership
- Projects, tasks, comments, and file attachments
- Per-project activity feed
- React SPA covering login, projects, board, archive, and team views

## Stack

- **`Meridian_Client/`** — React 19 + Vite (port 8080)
- **`Meridian_Server/`** — FastAPI + SQLAlchemy (port 8000)
- **Postgres 16** — database (port 5432)

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Client: http://localhost:8080
- API: http://localhost:8000 (Swagger at `/docs`)
- DB health: http://localhost:8000/health/db

`.env.example` covers DB credentials, JWT/session secrets, and optional OAuth client IDs.

## Local dev without Docker

Backend (from `Meridian_Server/`):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
```

Frontend (from `Meridian_Client/`):

```bash
npm install
npm run dev
npm run build
npm run lint
```

## Project layout

```
Meridian_Client/    React SPA (pages/, components/, api/, auth/)
Meridian_Server/    FastAPI app
  app/api/routes/   HTTP layer — request parsing, status codes
  app/services/     Business logic, no FastAPI imports
  app/repositories/ SQLAlchemy queries
  app/models/       ORM tables
  app/schemas/      Pydantic request/response models
docker-compose.yml  Local full-stack orchestration
render.yaml         Render static-site config for the client
```

## Configuration

All knobs live in `.env` (see `.env.example`). The ones that meaningfully change behavior:

- `INITIAL_ADMIN_EMAIL` — grants the admin role on startup to the matching user, if they exist.
- `OAUTH_REDIRECT_BASE` / `FRONTEND_BASE_URL` — set these to your public URLs when deploying.
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` and `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` — leave blank to disable that provider.

## Deployment

`render.yaml` deploys `Meridian_Client/` as a Render static site with an SPA rewrite to `/index.html`. The API server and Postgres are deployed separately; point the client at the API by setting `VITE_API_URL` at build time.

## More

Architecture notes for contributors live in [`CLAUDE.md`](./CLAUDE.md). Licensed under the terms in [`LICENSE`](./LICENSE).
