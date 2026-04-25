from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from ..models.task import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus = TaskStatus.backlog
    priority: TaskPriority = TaskPriority.medium
    assignee_id: int | None = None
    tags: list[str] = []
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = None
    tags: list[str] | None = None
    due_date: date | None = None


class TaskMove(BaseModel):
    status: TaskStatus
    before_task_id: int | None = None
    after_task_id: int | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    number: int
    code: str
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: int | None
    assignee_initials: str | None
    tags: list[str]
    due_date: date | None
    sort_key: float
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    comment_count: int
    attachment_count: int

    @classmethod
    def from_task(cls, task) -> "TaskRead":
        initials = None
        if task.assignee is not None:
            parts = task.assignee.name.split()
            if len(parts) >= 2:
                initials = (parts[0][0] + parts[-1][0]).upper()
            elif parts:
                initials = parts[0][:2].upper()
        code = f"{task.project.code}-{task.number}" if task.project else str(task.number)
        return cls(
            id=task.id,
            project_id=task.project_id,
            number=task.number,
            code=code,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            assignee_id=task.assignee_id,
            assignee_initials=initials,
            tags=list(task.tags or []),
            due_date=task.due_date,
            sort_key=task.sort_key,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            comment_count=len(task.comments or []),
            attachment_count=len(task.attachments or []),
        )


class BoardColumn(BaseModel):
    status: TaskStatus
    tasks: list[TaskRead]


class BoardRead(BaseModel):
    columns: list[BoardColumn]


