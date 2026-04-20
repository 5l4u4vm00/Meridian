from sqlalchemy.orm import Session

from ..repositories import role_repository, user_repository

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": ["users:read", "users:manage", "content:read", "content:write"],
    "editor": ["users:read", "content:read", "content:write"],
    "user": ["users:read", "content:read"],
}

DEFAULT_ROLE = "user"
ADMIN_ROLE = "admin"


def seed_rbac(db: Session, *, initial_admin_email: str | None = None) -> None:
    for role_name, perms in ROLE_PERMISSIONS.items():
        role_repository.ensure_role(db, role_name, perms)

    if initial_admin_email:
        user = user_repository.get_by_email(db, initial_admin_email)
        if user is not None:
            role_repository.assign_role(db, user, ADMIN_ROLE)
