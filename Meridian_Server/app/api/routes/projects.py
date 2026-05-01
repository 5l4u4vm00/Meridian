from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...models.user import User
from ...schemas.activity import ActivityEventRead
from ...schemas.project import (
    MemberRead,
    ProjectCreate,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)
from ...schemas.stats import ProjectStats, TeamMemberLoad
from ...services import activity_service, project_service, stats_service
from ...services.project_service import ProjectError
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        project = project_service.create_project(db, payload, created_by_id=user.id)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectSummary])
def list_projects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return project_service.list_project_summaries(db)


@router.get("/{code}", response_model=ProjectRead)
def get_project(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        project = project_service.get_by_code(db, code)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return ProjectRead.model_validate(project)


@router.patch("/{code}", response_model=ProjectRead)
def update_project(
    code: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        project = project_service.update_project(db, code, payload)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return ProjectRead.model_validate(project)


@router.delete("/{code}", status_code=204)
def delete_project(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        project_service.delete_project(db, code)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{code}/members", response_model=list[MemberRead])
def list_members(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return project_service.list_members(db, code)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{code}/stats", response_model=ProjectStats)
def get_stats(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return stats_service.get_project_stats(db, code)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{code}/workload", response_model=list[TeamMemberLoad])
def get_workload(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return stats_service.get_team_load(db, code)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{code}/activity", response_model=list[ActivityEventRead])
def get_activity(
    code: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        events = activity_service.list_for_project(db, code, limit=limit)
    except ProjectError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return [ActivityEventRead.from_event(e) for e in events]
