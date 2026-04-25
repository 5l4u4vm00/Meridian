from datetime import datetime

from pydantic import BaseModel, ConfigDict


def _initials(name: str | None) -> str | None:
    if not name:
        return None
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return parts[0][:2].upper() if parts else None


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    filename: str
    size_bytes: int
    mime_type: str
    url: str
    uploaded_by_id: int
    uploader_name: str | None
    uploader_initials: str | None
    created_at: datetime

    @classmethod
    def from_attachment(cls, att) -> "AttachmentRead":
        uploader_name = att.uploader.name if att.uploader is not None else None
        return cls(
            id=att.id,
            task_id=att.task_id,
            filename=att.filename,
            size_bytes=att.size_bytes,
            mime_type=att.mime_type,
            url=f"/attachments/{att.id}/download",
            uploaded_by_id=att.uploaded_by_id,
            uploader_name=uploader_name,
            uploader_initials=_initials(uploader_name),
            created_at=att.created_at,
        )
