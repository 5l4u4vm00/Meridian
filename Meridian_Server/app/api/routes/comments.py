from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...models.user import User
from ...schemas.comment import CommentCreate, CommentRead
from ...services import comment_service
from ...services.comment_service import CommentError
from ..deps import get_current_user, get_db

router = APIRouter(tags=["comments"])


@router.get("/tasks/{task_id}/comments", response_model=list[CommentRead])
def list_task_comments(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        comments = comment_service.list_comments(db, task_id)
    except CommentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return [CommentRead.from_comment(c) for c in comments]


@router.post("/tasks/{task_id}/comments", response_model=CommentRead, status_code=201)
def create_task_comment(
    task_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        comment = comment_service.create_comment(
            db, task_id=task_id, body=payload.body, actor_id=user.id
        )
    except CommentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return CommentRead.from_comment(comment)
