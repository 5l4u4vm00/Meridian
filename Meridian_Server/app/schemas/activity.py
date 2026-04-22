from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int
    actor_initials: str | None
    actor_name: str | None
    project_id: int
    task_id: int | None
    task_code: str | None
    verb: str
    meta: dict
    created_at: datetime

    @classmethod
    def from_event(cls, event) -> "ActivityEventRead":
        initials = None
        actor_name = None
        if event.actor is not None:
            actor_name = event.actor.name
            parts = event.actor.name.split()
            if len(parts) >= 2:
                initials = (parts[0][0] + parts[-1][0]).upper()
            elif parts:
                initials = parts[0][:2].upper()
        task_code = None
        if event.task is not None and event.task.project is not None:
            task_code = f"{event.task.project.code}-{event.task.number}"
        return cls(
            id=event.id,
            actor_id=event.actor_id,
            actor_initials=initials,
            actor_name=actor_name,
            project_id=event.project_id,
            task_id=event.task_id,
            task_code=task_code,
            verb=event.verb,
            meta=dict(event.meta or {}),
            created_at=event.created_at,
        )
