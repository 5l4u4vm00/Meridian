from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.activity_event import ActivityEvent


def create(
    db: Session,
    *,
    actor_id: int,
    project_id: int,
    task_id: int | None,
    verb: str,
    meta: dict | None = None,
    commit: bool = True,
) -> ActivityEvent:
    event = ActivityEvent(
        actor_id=actor_id,
        project_id=project_id,
        task_id=task_id,
        verb=verb,
        meta=dict(meta or {}),
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    else:
        db.flush()
    return event


def list_for_project(db: Session, project_id: int, limit: int = 20) -> list[ActivityEvent]:
    return list(
        db.scalars(
            select(ActivityEvent)
            .where(ActivityEvent.project_id == project_id)
            .order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc())
            .limit(limit)
        )
    )
