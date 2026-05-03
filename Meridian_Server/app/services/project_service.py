from sqlalchemy.orm import Session

from ..models.project import Project
from ..models.user import User
from ..repositories import project_repository, user_repository
from ..schemas.project import ProjectCreate, ProjectSummary, ProjectUpdate
from . import authz
from .authz import AuthzError


class ProjectError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_project(db: Session, payload: ProjectCreate, *, created_by_id: int) -> Project:
    if project_repository.get_by_code(db, payload.code) is not None:
        raise ProjectError(f"project code '{payload.code}' already exists", status_code=409)
    project = project_repository.create(
        db,
        code=payload.code,
        name=payload.name,
        color=payload.color,
        deadline=payload.deadline,
        lead_id=payload.lead_id,
        created_by_id=created_by_id,
    )
    project_repository.add_member(
        db, project_id=project.id, user_id=created_by_id, role=authz.LEAD_ROLE
    )
    return project


def list_projects(db: Session) -> list[Project]:
    return project_repository.list_all(db)


def list_project_summaries(db: Session, *, user: User) -> list[ProjectSummary]:
    user_id = None if authz.is_admin(user) else user.id
    return [
        ProjectSummary(**row)
        for row in project_repository.list_with_summary(db, user_id=user_id)
    ]


def get_by_code(db: Session, code: str) -> Project:
    project = project_repository.get_by_code(db, code)
    if project is None:
        raise ProjectError("project not found", status_code=404)
    return project


def get_project_for_user(db: Session, code: str, *, user: User) -> Project:
    project, _ = authz.require_member_by_code(db, code, user)
    return project


def update_project(
    db: Session, code: str, payload: ProjectUpdate, *, user: User
) -> Project:
    project, _ = authz.require_lead_by_code(db, code, user)
    changes = payload.model_dump(exclude_unset=True)

    if "lead_id" in changes:
        new_lead_id = changes["lead_id"]
        if new_lead_id is None:
            raise ProjectError("lead_id is required", status_code=400)
        if user_repository.get(db, new_lead_id) is None:
            raise ProjectError("user not found", status_code=404)
        current_leads = [
            m for m in project_repository.list_members(db, project.id)
            if m["role"] == authz.LEAD_ROLE and m["id"] != new_lead_id
        ]
        if not project_repository.set_member_role(
            db, project_id=project.id, user_id=new_lead_id, role=authz.LEAD_ROLE
        ):
            raise ProjectError(
                "new leader must be a project member", status_code=400
            )
        for m in current_leads:
            project_repository.set_member_role(
                db,
                project_id=project.id,
                user_id=m["id"],
                role=authz.MEMBER_ROLE,
            )

    for k, v in changes.items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return project


def task_count(db: Session, project_id: int) -> int:
    return project_repository.task_count(db, project_id)


def delete_project(db: Session, code: str, *, user: User) -> None:
    project, _ = authz.require_lead_by_code(db, code, user)
    project_repository.delete(db, project)


def list_members(db: Session, code: str, *, user: User) -> list[dict]:
    project, _ = authz.require_member_by_code(db, code, user)
    return project_repository.list_members(db, project.id)


def add_member(
    db: Session,
    code: str,
    user_id: int,
    role: str = authz.MEMBER_ROLE,
    *,
    current_user: User,
) -> dict:
    project, _ = authz.require_lead_by_code(db, code, current_user)
    target = user_repository.get(db, user_id)
    if target is None:
        raise ProjectError("user not found", status_code=404)
    project_repository.add_member(
        db, project_id=project.id, user_id=target.id, role=role
    )
    existing = next(
        (m for m in project_repository.list_members(db, project.id) if m["id"] == target.id),
        None,
    )
    if existing is not None:
        return existing
    return {"id": target.id, "name": target.name, "email": target.email, "role": role}


__all__ = [
    "ProjectError",
    "AuthzError",
    "create_project",
    "list_projects",
    "list_project_summaries",
    "get_by_code",
    "get_project_for_user",
    "update_project",
    "delete_project",
    "list_members",
    "add_member",
    "task_count",
]
