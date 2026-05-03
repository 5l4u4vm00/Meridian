from sqlalchemy.orm import Session

from ..models.activity_event import ActivityEvent
from ..models.user import User
from ..repositories import activity_repository
from . import authz


def list_for_project(
    db: Session, code: str, *, user: User, limit: int = 20
) -> list[ActivityEvent]:
    project, _ = authz.require_member_by_code(db, code, user)
    return activity_repository.list_for_project(db, project.id, limit=limit)
