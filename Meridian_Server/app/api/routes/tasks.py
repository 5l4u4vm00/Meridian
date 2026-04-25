from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...models.user import User
from ...schemas.attachment import AttachmentRead
from ...schemas.comment import CommentRead
from ...schemas.task import BoardColumn, BoardRead, TaskCreate, TaskMove, TaskRead, TaskUpdate
from ...models.task import TaskStatus
from ...services import attachment_service, comment_service, task_service
from ...services.task_service import TaskError
from ..deps import get_current_user, get_db

router = APIRouter(tags=["tasks"])


@router.get("/projects/{code}/tasks", response_model=BoardRead)
def list_project_tasks(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        tasks = task_service.list_tasks_for_project(db, code)
    except TaskError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    buckets: dict[TaskStatus, list[TaskRead]] = {s: [] for s in TaskStatus}
    for t in tasks:
        buckets[t.status].append(TaskRead.from_task(t))
    return BoardRead(
        columns=[BoardColumn(status=s, tasks=buckets[s]) for s in TaskStatus]
    )


@router.post("/projects/{code}/tasks", response_model=TaskRead, status_code=201)
def create_task(
    code: str,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        task = task_service.create_task(
            db, project_code=code, payload=payload, actor_id=user.id
        )
    except TaskError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TaskRead.from_task(task)


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        task = task_service.get_task(db, task_id)
    except TaskError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TaskRead.from_task(task)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        task = task_service.update_task(db, task_id, payload, actor_id=user.id)
    except TaskError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TaskRead.from_task(task)


@router.get("/tasks/{task_id}/detail")
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        task = task_service.get_task(db, task_id)
    except TaskError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    comments = comment_service.list_comments(db, task_id)
    attachments = attachment_service.list_attachments(db, task_id)
    return {
        "task": TaskRead.from_task(task),
        "comments": [CommentRead.from_comment(c) for c in comments],
        "attachments": [AttachmentRead.from_attachment(a) for a in attachments],
    }


@router.post("/tasks/{task_id}/move", response_model=TaskRead)
def move_task(
    task_id: int,
    payload: TaskMove,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        task = task_service.move_task(db, task_id, payload, actor_id=user.id)
    except TaskError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TaskRead.from_task(task)
