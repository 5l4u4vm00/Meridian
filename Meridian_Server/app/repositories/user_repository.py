from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user import User


def create(db: Session, *, email: str, name: str) -> User:
    user = User(email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def list_all(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))
