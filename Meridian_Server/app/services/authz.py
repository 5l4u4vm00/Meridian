from sqlalchemy.orm import Session

from ..core.seed import ADMIN_ROLE
from ..models.project import Project
from ..models.project_member import ProjectMember
from ..models.user import User
from ..repositories import project_repository

LEAD_ROLE = "lead"
MEMBER_ROLE = "member"


class AuthzError(Exception):
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def is_admin(user: User) -> bool:
    return user.role is not None and user.role.name == ADMIN_ROLE


def get_membership(db: Session, project_id: int, user_id: int) -> ProjectMember | None:
    return db.get(ProjectMember, (project_id, user_id))


def require_member_for_project(
    db: Session, project: Project, user: User
) -> ProjectMember | None:
    """Returns the user's ProjectMember row, or None if user is a global admin.
    Raises 404 (not 403) for non-members so project existence isn't leaked."""
    if is_admin(user):
        return None
    membership = get_membership(db, project.id, user.id)
    if membership is None:
        raise AuthzError("project not found", status_code=404)
    return membership


def require_lead_for_project(
    db: Session, project: Project, user: User
) -> ProjectMember | None:
    membership = require_member_for_project(db, project, user)
    if membership is None:
        return None  # admin bypass
    if membership.role != LEAD_ROLE:
        raise AuthzError("requires project lead role", status_code=403)
    return membership


def require_member_by_code(
    db: Session, code: str, user: User
) -> tuple[Project, ProjectMember | None]:
    project = project_repository.get_by_code(db, code)
    if project is None:
        raise AuthzError("project not found", status_code=404)
    membership = require_member_for_project(db, project, user)
    return project, membership


def require_lead_by_code(
    db: Session, code: str, user: User
) -> tuple[Project, ProjectMember | None]:
    project, membership = require_member_by_code(db, code, user)
    if membership is None:
        return project, None
    if membership.role != LEAD_ROLE:
        raise AuthzError("requires project lead role", status_code=403)
    return project, membership
