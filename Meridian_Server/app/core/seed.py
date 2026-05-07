from sqlalchemy.orm import Session

from ..models.role import Role
from ..repositories import role_repository, user_repository
from . import permissions as perms

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [perms.USERS_READ, perms.USERS_MANAGE, perms.CONTENT_READ, perms.CONTENT_WRITE],
    "user": [perms.USERS_READ, perms.CONTENT_READ],
}

DEFAULT_ROLE = "user"
ADMIN_ROLE = "admin"

_RETIRED_ROLES = ("editor",)


def seed_rbac(db: Session, *, initial_admin_email: str | None = None) -> None:
    for role_name, role_perms in ROLE_PERMISSIONS.items():
        role_repository.ensure_role(db, role_name, role_perms)

    for retired in _RETIRED_ROLES:
        stale = db.query(Role).filter(Role.name == retired).first()
        if stale is not None:
            db.delete(stale)
            db.commit()

    if initial_admin_email:
        user = user_repository.get_by_email(db, initial_admin_email)
        if user is not None:
            role_repository.assign_role(db, user, ADMIN_ROLE)
