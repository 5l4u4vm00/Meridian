from sqlalchemy.orm import Session

from ..models.activity_event import ActivityEvent
from ..repositories import activity_repository, project_repository
from .project_service import ProjectError


def list_for_project(db: Session, code: str, limit: int = 20) -> list[ActivityEvent]:
    project = project_repository.get_by_code(db, code)
    if project is None:
        raise ProjectError("project not found", status_code=404)
    return activity_repository.list_for_project(db, project.id, limit=limit)
