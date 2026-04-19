from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.refresh_token import RefreshToken


def create(db: Session, *, user_id: int, jti: str, expires_at: datetime) -> RefreshToken:
    row = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_active(db: Session, jti: str) -> RefreshToken | None:
    row = db.scalars(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    if row is None or row.revoked_at is not None:
        return None
    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    return row


def revoke(db: Session, jti: str) -> None:
    row = db.scalars(select(RefreshToken).where(RefreshToken.jti == jti)).first()
    if row is None or row.revoked_at is not None:
        return
    row.revoked_at = datetime.now(timezone.utc)
    db.commit()
