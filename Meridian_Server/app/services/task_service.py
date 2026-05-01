from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.task import Task, TaskStatus
from ..repositories import activity_repository, project_repository, task_repository
from ..schemas.task import TaskCreate, TaskMove, TaskUpdate


class TaskError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_task(
    db: Session, *, project_code: str, payload: TaskCreate, actor_id: int
) -> Task:
    project = project_repository.get_by_code(db, project_code)
    if project is None:
        raise TaskError("project not found", status_code=404)
    task = task_repository.create(
        db,
        project_id=project.id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        tags=payload.tags,
        due_date=payload.due_date,
        created_by_id=actor_id,
    )
    activity_repository.create(
        db,
        actor_id=actor_id,
        project_id=project.id,
        task_id=task.id,
        verb="created",
        meta={"status": task.status.value, "title": task.title},
    )
    if task.status == TaskStatus.shipped:
        activity_repository.create(
            db,
            actor_id=actor_id,
            project_id=project.id,
            task_id=task.id,
            verb="completed",
            meta={},
        )
    return task


def list_tasks_for_project(db: Session, project_code: str) -> list[Task]:
    project = project_repository.get_by_code(db, project_code)
    if project is None:
        raise TaskError("project not found", status_code=404)
    return task_repository.list_for_project(db, project.id)


def list_tasks_for_user(
    db: Session, user_id: int, *, include_shipped: bool = False
) -> list[Task]:
    return task_repository.list_for_assignee(
        db, user_id, include_shipped=include_shipped
    )


def get_task(db: Session, task_id: int) -> Task:
    task = task_repository.get(db, task_id)
    if task is None:
        raise TaskError("task not found", status_code=404)
    return task


def update_task(db: Session, task_id: int, payload: TaskUpdate, *, actor_id: int) -> Task:
    task = get_task(db, task_id)
    changes = payload.model_dump(exclude_unset=True)
    updated = task_repository.update(db, task, **changes)
    activity_repository.create(
        db,
        actor_id=actor_id,
        project_id=updated.project_id,
        task_id=updated.id,
        verb="updated",
        meta={"fields": sorted(changes.keys())},
    )
    return updated


def delete_task(db: Session, task_id: int, *, actor_id: int) -> None:
    task = get_task(db, task_id)
    task_repository.delete(db, task)


def move_task(db: Session, task_id: int, payload: TaskMove, *, actor_id: int) -> Task:
    task = get_task(db, task_id)
    from_status = task.status
    new_sort_key = task_repository.compute_move_sort_key(
        db,
        project_id=task.project_id,
        status=payload.status,
        before_task_id=payload.before_task_id,
        after_task_id=payload.after_task_id,
        moving_task_id=task.id,
    )
    changes = {"status": payload.status, "sort_key": new_sort_key}
    was_shipped = task.status == TaskStatus.shipped
    will_be_shipped = payload.status == TaskStatus.shipped
    if will_be_shipped and not was_shipped:
        changes["completed_at"] = datetime.now(timezone.utc)
    elif not will_be_shipped and was_shipped:
        changes["completed_at"] = None
    updated = task_repository.update(db, task, **changes)

    if from_status != updated.status:
        activity_repository.create(
            db,
            actor_id=actor_id,
            project_id=updated.project_id,
            task_id=updated.id,
            verb="moved",
            meta={"from": from_status.value, "to": updated.status.value},
        )
        if will_be_shipped and not was_shipped:
            activity_repository.create(
                db,
                actor_id=actor_id,
                project_id=updated.project_id,
                task_id=updated.id,
                verb="completed",
                meta={},
            )
    return updated
