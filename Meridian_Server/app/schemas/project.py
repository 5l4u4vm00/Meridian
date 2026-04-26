from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    code: str = Field(min_length=2, max_length=8, pattern=r"^[A-Z0-9]+$")
    name: str = Field(min_length=1, max_length=255)
    color: str = Field(default="#c4511c", max_length=16)
    deadline: date | None = None
    lead_id: int | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    deadline: date | None = None
    lead_id: int | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    color: str
    deadline: date | None
    lead_id: int | None
    created_by_id: int
    created_at: datetime


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    color: str
    task_count: int
    open_count: int
    shipped_count: int
    last_activity: datetime | None = None
