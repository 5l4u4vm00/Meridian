from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.oauth_account import OAuthAccount


def get_by_provider(db: Session, provider: str, provider_account_id: str) -> OAuthAccount | None:
    return db.scalars(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == provider_account_id,
        )
    ).first()


def link(db: Session, *, user_id: int, provider: str, provider_account_id: str) -> OAuthAccount:
    row = OAuthAccount(
        user_id=user_id,
        provider=provider,
        provider_account_id=provider_account_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
