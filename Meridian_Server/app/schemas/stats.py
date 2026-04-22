from pydantic import BaseModel


class ProjectStats(BaseModel):
    open: int
    shipped: int
    overdue: int
    velocity: int  # tasks shipped in last 7 days


class TeamMemberLoad(BaseModel):
    user_id: int
    initials: str
    name: str
    role: str | None
    active_tasks: int
    load_pct: int
