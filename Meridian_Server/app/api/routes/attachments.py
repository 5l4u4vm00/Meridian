from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...models.user import User
from ...repositories import attachment_repository
from ...schemas.attachment import AttachmentRead
from ...services import attachment_service
from ...services.attachment_service import AttachmentError
from ..deps import get_current_user, get_db

router = APIRouter(tags=["attachments"])


@router.get("/tasks/{task_id}/attachments", response_model=list[AttachmentRead])
def list_task_attachments(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        attachments = attachment_service.list_attachments(db, task_id)
    except AttachmentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return [AttachmentRead.from_attachment(a) for a in attachments]


@router.post(
    "/tasks/{task_id}/attachments", response_model=AttachmentRead, status_code=201
)
async def create_task_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await file.read()
    try:
        att = attachment_service.create_attachment(
            db,
            task_id=task_id,
            data=data,
            filename=file.filename or "untitled",
            mime_type=file.content_type,
            actor_id=user.id,
        )
    except AttachmentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return AttachmentRead.from_attachment(att)


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        att = attachment_service.get_attachment(db, attachment_id)
    except AttachmentError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    if not att.storage_key:
        raise HTTPException(status_code=404, detail="attachment has no stored file")
    path = attachment_repository.blob_path(att.storage_key)
    if not path.exists():
        raise HTTPException(status_code=404, detail="file missing on disk")
    return FileResponse(
        path,
        media_type=att.mime_type or "application/octet-stream",
        filename=att.filename,
    )
