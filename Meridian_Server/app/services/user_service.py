from sqlalchemy.orm import Session

from ..models.user import User
from ..repositories import role_repository, user_repository
from ..schemas.user import UserCreate


class UserServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_user(db: Session, payload: UserCreate) -> User:
    return user_repository.create(db, email=payload.email, name=payload.name)


def get_user(db: Session, user_id: int) -> User | None:
    return user_repository.get(db, user_id)


def list_users(db: Session) -> list[User]:
    return user_repository.list_all(db)


def set_user_role(db: Session, user_id: int, role_name: str) -> User:
    user = user_repository.get(db, user_id)
    if user is None:
        raise UserServiceError("user not found", status_code=404)
    if role_repository.get_role_by_name(db, role_name) is None:
        raise UserServiceError(f"unknown role: {role_name}", status_code=400)
    return role_repository.assign_role(db, user, role_name)
