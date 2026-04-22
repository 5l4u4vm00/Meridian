from sqlalchemy.orm import Session

from ..models.project import Project
from ..repositories import project_repository
from ..schemas.project import ProjectCreate, ProjectUpdate


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
    project_repository.add_member(db, project_id=project.id, user_id=created_by_id, role="lead")
    return project


def list_projects(db: Session) -> list[Project]:
    return project_repository.list_all(db)


def get_by_code(db: Session, code: str) -> Project:
    project = project_repository.get_by_code(db, code)
    if project is None:
        raise ProjectError("project not found", status_code=404)
    return project


def update_project(db: Session, code: str, payload: ProjectUpdate) -> Project:
    project = get_by_code(db, code)
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return project


def task_count(db: Session, project_id: int) -> int:
    return project_repository.task_count(db, project_id)
