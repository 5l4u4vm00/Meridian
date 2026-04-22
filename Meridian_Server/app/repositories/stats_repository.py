from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.project_member import ProjectMember
from ..models.task import Task, TaskStatus
from ..models.user import User


def counts_by_status(db: Session, project_id: int) -> dict[TaskStatus, int]:
    rows = db.execute(
        select(Task.status, func.count())
        .where(Task.project_id == project_id)
        .group_by(Task.status)
    ).all()
    out = {s: 0 for s in TaskStatus}
    for status, count in rows:
        out[status] = int(count)
    return out


def overdue_count(db: Session, project_id: int) -> int:
    today = date.today()
    return int(
        db.scalar(
            select(func.count())
            .select_from(Task)
            .where(
                Task.project_id == project_id,
                Task.due_date.is_not(None),
                Task.due_date < today,
                Task.status != TaskStatus.shipped,
            )
        )
        or 0
    )


def shipped_since(db: Session, project_id: int, days: int = 7) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return int(
        db.scalar(
            select(func.count())
            .select_from(Task)
            .where(
                Task.project_id == project_id,
                Task.completed_at.is_not(None),
                Task.completed_at >= cutoff,
            )
        )
        or 0
    )


def active_tasks_by_user(db: Session, project_id: int) -> dict[int, int]:
    """Count of non-shipped tasks assigned to each user in the project."""
    rows = db.execute(
        select(Task.assignee_id, func.count())
        .where(
            Task.project_id == project_id,
            Task.assignee_id.is_not(None),
            Task.status != TaskStatus.shipped,
        )
        .group_by(Task.assignee_id)
    ).all()
    return {int(uid): int(count) for uid, count in rows if uid is not None}


def project_members(db: Session, project_id: int) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .join(ProjectMember, ProjectMember.user_id == User.id)
            .where(ProjectMember.project_id == project_id)
            .order_by(User.id)
        )
    )
