from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


def _initials(name: str | None) -> str | None:
    if not name:
        return None
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return parts[0][:2].upper() if parts else None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    author_id: int
    author_name: str | None
    author_initials: str | None
    body: str
    created_at: datetime

    @classmethod
    def from_comment(cls, comment) -> "CommentRead":
        author_name = comment.author.name if comment.author is not None else None
        return cls(
            id=comment.id,
            task_id=comment.task_id,
            author_id=comment.author_id,
            author_name=author_name,
            author_initials=_initials(author_name),
            body=comment.body,
            created_at=comment.created_at,
        )
