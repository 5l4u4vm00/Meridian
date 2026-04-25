from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.attachment import Attachment


def _storage_dir() -> Path:
    p = Path(settings.attachments_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_blob(data: bytes) -> str:
    key = uuid4().hex
    (_storage_dir() / f"{key}.bin").write_bytes(data)
    return key


def blob_path(storage_key: str) -> Path:
    return _storage_dir() / f"{storage_key}.bin"


def create(
    db: Session,
    *,
    task_id: int,
    uploaded_by_id: int,
    filename: str,
    size_bytes: int,
    mime_type: str,
    storage_key: str,
) -> Attachment:
    att = Attachment(
        task_id=task_id,
        uploaded_by_id=uploaded_by_id,
        filename=filename,
        size_bytes=size_bytes,
        mime_type=mime_type,
        storage_key=storage_key,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


def get(db: Session, attachment_id: int) -> Attachment | None:
    return db.get(Attachment, attachment_id)


def list_for_task(db: Session, task_id: int) -> list[Attachment]:
    return list(
        db.scalars(
            select(Attachment)
            .where(Attachment.task_id == task_id)
            .order_by(Attachment.created_at.asc(), Attachment.id.asc())
        )
    )
