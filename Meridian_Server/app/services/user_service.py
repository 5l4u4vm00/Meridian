from sqlalchemy.orm import Session

from ..models.user import User
from ..repositories import user_repository
from ..schemas.user import UserCreate


def create_user(db: Session, payload: UserCreate) -> User:
    return user_repository.create(db, email=payload.email, name=payload.name)


def get_user(db: Session, user_id: int) -> User | None:
    return user_repository.get(db, user_id)


def list_users(db: Session) -> list[User]:
    return user_repository.list_all(db)
