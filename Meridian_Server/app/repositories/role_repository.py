from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.role import Permission, Role
from ..models.user import User


def get_role_by_name(db: Session, name: str) -> Role | None:
    return db.scalars(select(Role).where(Role.name == name)).first()


def get_permission_by_name(db: Session, name: str) -> Permission | None:
    return db.scalars(select(Permission).where(Permission.name == name)).first()


def ensure_permission(db: Session, name: str, description: str | None = None) -> Permission:
    existing = get_permission_by_name(db, name)
    if existing is not None:
        return existing
    perm = Permission(name=name, description=description)
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return perm


def ensure_role(db: Session, name: str, permissions: list[str] | None = None) -> Role:
    role = get_role_by_name(db, name)
    if role is None:
        role = Role(name=name)
        db.add(role)
        db.flush()
    if permissions:
        existing_names = {p.name for p in role.permissions}
        for pname in permissions:
            if pname in existing_names:
                continue
            perm = ensure_permission(db, pname)
            role.permissions.append(perm)
    db.commit()
    db.refresh(role)
    return role


def assign_role(db: Session, user: User, role_name: str) -> User:
    role = get_role_by_name(db, role_name)
    if role is None:
        raise ValueError(f"role {role_name!r} does not exist")
    user.role_id = role.id
    db.commit()
    db.refresh(user)
    return user
