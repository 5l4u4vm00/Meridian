from sqlalchemy.orm import Session

from ..models.comment import Comment
from ..repositories import activity_repository, comment_repository, task_repository


class CommentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_task_or_raise(db: Session, task_id: int):
    task = task_repository.get(db, task_id)
    if task is None:
        raise CommentError("task not found", status_code=404)
    return task


def list_comments(db: Session, task_id: int) -> list[Comment]:
    _get_task_or_raise(db, task_id)
    return comment_repository.list_for_task(db, task_id)


def create_comment(db: Session, *, task_id: int, body: str, actor_id: int) -> Comment:
    task = _get_task_or_raise(db, task_id)
    comment = comment_repository.create(
        db, task_id=task.id, author_id=actor_id, body=body
    )
    activity_repository.create(
        db,
        actor_id=actor_id,
        project_id=task.project_id,
        task_id=task.id,
        verb="commented",
        meta={"preview": body[:80]},
    )
    return comment
