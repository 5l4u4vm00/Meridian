from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from . import models  # noqa: F401  (register models with Base metadata)
from .api.routes import auth, health, users
from .core.config import settings
from .core.db import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)

    # Dev-only: create tables on startup. Replace with Alembic before production.
    # Swallow connection errors so tests (which use their own engine via dependency
    # overrides) can import the app without a running Postgres.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    app.include_router(health.router)
    app.include_router(users.router)
    app.include_router(auth.router)

    @app.get("/")
    def root():
        return {"service": settings.app_name, "status": "ok"}

    return app


app = create_app()
