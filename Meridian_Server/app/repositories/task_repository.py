from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.task import Task, TaskPriority, TaskStatus


def _next_number(db: Session, project_id: int) -> int:
    current = db.scalar(
        select(func.coalesce(func.max(Task.number), 0)).where(Task.project_id == project_id)
    )
    return int(current or 0) + 1


def _next_sort_key(db: Session, project_id: int, status: TaskStatus) -> float:
    current = db.scalar(
        select(func.coalesce(func.max(Task.sort_key), 0.0)).where(
            Task.project_id == project_id, Task.status == status
        )
    )
    return float(current or 0.0) + 1.0


def create(
    db: Session,
    *,
    project_id: int,
    title: str,
    description: str | None,
    status: TaskStatus,
    priority: TaskPriority,
    assignee_id: int | None,
    tags: list[str],
    due_date,
    created_by_id: int,
) -> Task:
    number = _next_number(db, project_id)
    sort_key = _next_sort_key(db, project_id, status)
    task = Task(
        project_id=project_id,
        number=number,
        title=title,
        description=description,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        tags=list(tags or []),
        due_date=due_date,
        sort_key=sort_key,
        created_by_id=created_by_id,
    )
    if status == TaskStatus.shipped:
        task.completed_at = datetime.now(timezone.utc)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def list_for_project(db: Session, project_id: int) -> list[Task]:
    return list(
        db.scalars(
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.status, Task.sort_key, Task.id)
        )
    )


def update(db: Session, task: Task, **changes) -> Task:
    for k, v in changes.items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return task


def compute_move_sort_key(
    db: Session,
    *,
    project_id: int,
    status: TaskStatus,
    before_task_id: int | None,
    after_task_id: int | None,
    moving_task_id: int,
) -> float:
    """Compute a sort_key that places a task between before/after siblings.

    `before_task_id`: the task that should end up directly above the moved task.
    `after_task_id`: the task that should end up directly below the moved task.
    If both are None, append to bottom of the column.
    """
    before = db.get(Task, before_task_id) if before_task_id else None
    after = db.get(Task, after_task_id) if after_task_id else None

    # Ignore siblings that are the moving task itself or not in the target column.
    def _valid(t):
        return (
            t is not None
            and t.id != moving_task_id
            and t.project_id == project_id
            and t.status == status
        )

    b = before.sort_key if _valid(before) else None
    a = after.sort_key if _valid(after) else None

    if b is not None and a is not None:
        return (b + a) / 2.0
    if b is not None:
        return b + 1.0
    if a is not None:
        return a - 1.0
    # Empty anchors — append to bottom.
    return _next_sort_key(db, project_id, status)
