from sqlalchemy.orm import Session

from ..models.comment import Comment
from ..models.user import User
from ..repositories import (
    activity_repository,
    comment_repository,
    project_repository,
    task_repository,
)
from . import authz


class CommentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _resolve_task(db: Session, task_id: int, user: User):
    task = task_repository.get(db, task_id)
    if task is None:
        raise CommentError("task not found", status_code=404)
    project = project_repository.get(db, task.project_id)
    if project is None:
        raise CommentError("task not found", status_code=404)
    authz.require_member_for_project(db, project, user)
    return task


def list_comments(db: Session, task_id: int, *, user: User) -> list[Comment]:
    _resolve_task(db, task_id, user)
    return comment_repository.list_for_task(db, task_id)


def create_comment(
    db: Session, *, task_id: int, body: str, actor: User
) -> Comment:
    task = _resolve_task(db, task_id, actor)
    comment = comment_repository.create(
        db, task_id=task.id, author_id=actor.id, body=body
    )
    activity_repository.create(
        db,
        actor_id=actor.id,
        project_id=task.project_id,
        task_id=task.id,
        verb="commented",
        meta={"preview": body[:80]},
    )
    return comment
