from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.attachment import Attachment
from ..repositories import activity_repository, attachment_repository, task_repository


class AttachmentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_task_or_raise(db: Session, task_id: int):
    task = task_repository.get(db, task_id)
    if task is None:
        raise AttachmentError("task not found", status_code=404)
    return task


def list_attachments(db: Session, task_id: int) -> list[Attachment]:
    _get_task_or_raise(db, task_id)
    return attachment_repository.list_for_task(db, task_id)


def get_attachment(db: Session, attachment_id: int) -> Attachment:
    att = attachment_repository.get(db, attachment_id)
    if att is None:
        raise AttachmentError("attachment not found", status_code=404)
    return att


def create_attachment(
    db: Session,
    *,
    task_id: int,
    data: bytes,
    filename: str,
    mime_type: str | None,
    actor_id: int,
) -> Attachment:
    task = _get_task_or_raise(db, task_id)
    if len(data) > settings.attachment_max_bytes:
        raise AttachmentError(
            f"file exceeds max size of {settings.attachment_max_bytes} bytes",
            status_code=413,
        )
    if not filename:
        raise AttachmentError("filename required", status_code=400)
    storage_key = attachment_repository.write_blob(data)
    att = attachment_repository.create(
        db,
        task_id=task.id,
        uploaded_by_id=actor_id,
        filename=filename,
        size_bytes=len(data),
        mime_type=mime_type or "application/octet-stream",
        storage_key=storage_key,
    )
    activity_repository.create(
        db,
        actor_id=actor_id,
        project_id=task.project_id,
        task_id=task.id,
        verb="attached",
        meta={"filename": filename},
    )
    return att
