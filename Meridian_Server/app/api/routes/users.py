from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...schemas.user import RoleAssign, UserCreate, UserRead
from ...services import user_service
from ...services.user_service import UserServiceError
from ..deps import get_db, require_role

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = user_service.create_user(db, payload)
    return UserRead.from_user(user)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.from_user(user)


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    return [UserRead.from_user(u) for u in user_service.list_users(db)]


@router.put(
    "/{user_id}/role",
    response_model=UserRead,
    dependencies=[Depends(require_role("admin"))],
)
def set_user_role(user_id: int, payload: RoleAssign, db: Session = Depends(get_db)):
    try:
        user = user_service.set_user_role(db, user_id, payload.role)
    except UserServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return UserRead.from_user(user)
