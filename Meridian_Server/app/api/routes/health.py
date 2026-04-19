from fastapi import APIRouter, HTTPException

from ...core.db import ping

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.get("/health/db")
def health_db():
    try:
        ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "healthy", "component": "db"}
