from datetime import datetime

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from ..models.project import Project
from ..models.project_member import ProjectMember
from ..models.task import Task, TaskStatus
from ..models.user import User


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
    return db.scalars(
        select(Project).where(Project.code == code, Project.is_deleted.is_(False))
    ).first()


def list_all(db: Session) -> list[Project]:
    return list(
        db.scalars(
            select(Project)
            .where(Project.is_deleted.is_(False))
            .order_by(Project.created_at)
        )
    )


def list_with_summary(db: Session) -> list[dict]:
    shipped_expr = func.sum(case((Task.status == TaskStatus.shipped, 1), else_=0))
    total_expr = func.count(Task.id)
    last_expr = func.max(Task.updated_at)
    stmt = (
        select(
            Project.id,
            Project.code,
            Project.name,
            Project.color,
            shipped_expr,
            total_expr,
            last_expr,
        )
        .outerjoin(
            Task,
            and_(Task.project_id == Project.id, Task.is_deleted.is_(False)),
        )
        .where(Project.is_deleted.is_(False))
        .group_by(Project.id, Project.code, Project.name, Project.color, Project.created_at)
        .order_by(Project.created_at)
    )
    out: list[dict] = []
    for pid, code, name, color, shipped, total, last in db.execute(stmt).all():
        shipped_n = int(shipped or 0)
        total_n = int(total or 0)
        out.append(
            {
                "id": pid,
                "code": code,
                "name": name,
                "color": color,
                "task_count": total_n,
                "open_count": total_n - shipped_n,
                "shipped_count": shipped_n,
                "last_activity": last,
            }
        )
    return out


def task_count(db: Session, project_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Task)
            .where(Task.project_id == project_id, Task.is_deleted.is_(False))
        )
        or 0
    )


def add_member(db: Session, *, project_id: int, user_id: int, role: str = "member") -> None:
    exists = db.get(ProjectMember, (project_id, user_id))
    if exists is not None:
        return
    db.add(ProjectMember(project_id=project_id, user_id=user_id, role=role))
    db.commit()


def list_members(db: Session, project_id: int) -> list[dict]:
    stmt = (
        select(User.id, User.name, User.email, ProjectMember.role)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .where(ProjectMember.project_id == project_id)
        .order_by(User.name)
    )
    return [
        {"id": uid, "name": name, "email": email, "role": role}
        for uid, name, email, role in db.execute(stmt).all()
    ]


def delete(db: Session, project: Project) -> None:
    project.is_deleted = True
    db.commit()
