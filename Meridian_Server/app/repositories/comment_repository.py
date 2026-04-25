from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.comment import Comment


def create(db: Session, *, task_id: int, author_id: int, body: str) -> Comment:
    comment = Comment(task_id=task_id, author_id=author_id, body=body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_for_task(db: Session, task_id: int) -> list[Comment]:
    return list(
        db.scalars(
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at.asc(), Comment.id.asc())
        )
    )
