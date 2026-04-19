from fastapi import FastAPI

from .api.routes import health, users
from .core.config import settings
from .core.db import Base, engine
from . import models  # noqa: F401  (register models with Base metadata)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # Dev-only: create tables on startup. Replace with Alembic before production.
    Base.metadata.create_all(bind=engine)

    app.include_router(health.router)
    app.include_router(users.router)

    @app.get("/")
    def root():
        return {"service": settings.app_name, "status": "ok"}

    return app


app = create_app()
