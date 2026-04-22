from sqlalchemy.orm import Session

from ..models.task import TaskStatus
from ..repositories import project_repository, stats_repository
from ..schemas.stats import ProjectStats, TeamMemberLoad
from .project_service import ProjectError

# Max active (non-shipped) tasks before a team member is considered at 100%.
WORKLOAD_CAP = 10


def _initials(name: str, fallback: str = "?") -> str:
    parts = (name or "").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return fallback


def get_project_stats(db: Session, code: str) -> ProjectStats:
    project = project_repository.get_by_code(db, code)
    if project is None:
        raise ProjectError("project not found", status_code=404)
    buckets = stats_repository.counts_by_status(db, project.id)
    shipped = buckets.get(TaskStatus.shipped, 0)
    total = sum(buckets.values())
    return ProjectStats(
        open=total - shipped,
        shipped=shipped,
        overdue=stats_repository.overdue_count(db, project.id),
        velocity=stats_repository.shipped_since(db, project.id, days=7),
    )


def get_team_load(db: Session, code: str) -> list[TeamMemberLoad]:
    project = project_repository.get_by_code(db, code)
    if project is None:
        raise ProjectError("project not found", status_code=404)
    counts = stats_repository.active_tasks_by_user(db, project.id)
    members = stats_repository.project_members(db, project.id)
    out: list[TeamMemberLoad] = []
    for m in members:
        active = counts.get(m.id, 0)
        pct = min(100, round(active / WORKLOAD_CAP * 100))
        out.append(
            TeamMemberLoad(
                user_id=m.id,
                initials=_initials(m.name, m.email[:2].upper() if m.email else "?"),
                name=m.name or m.email,
                role=m.role.name if m.role is not None else None,
                active_tasks=active,
                load_pct=pct,
            )
        )
    out.sort(key=lambda x: x.load_pct, reverse=True)
    return out
