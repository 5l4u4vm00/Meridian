from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.project import Project
from ..models.project_member import ProjectMember
from ..models.task import Task


def create(
    db: Session,
    *,
    code: str,
    name: str,
    color: str,
    deadline,
    lead_id: int | None,
    created_by_id: int,
) -> Project:
    project = Project(
        code=code,
        name=name,
        color=color,
        deadline=deadline,
        lead_id=lead_id,
        created_by_id=created_by_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def get_by_code(db: Session, code: str) -> Project | None:
    return db.scalars(select(Project).where(Project.code == code)).first()


def list_all(db: Session) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.created_at)))


def task_count(db: Session, project_id: int) -> int:
    return (
        db.scalar(select(func.count()).select_from(Task).where(Task.project_id == project_id))
        or 0
    )


def add_member(db: Session, *, project_id: int, user_id: int, role: str = "member") -> None:
    exists = db.get(ProjectMember, (project_id, user_id))
    if exists is not None:
        return
    db.add(ProjectMember(project_id=project_id, user_id=user_id, role=role))
    db.commit()
