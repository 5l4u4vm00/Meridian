import uuid

from sqlalchemy.orm import Session

from ..core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from ..models.user import User
from ..repositories import oauth_repository, refresh_token_repository, user_repository
from ..schemas.auth import AccessToken, RegisterRequest, TokenPair


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register(db: Session, payload: RegisterRequest) -> User:
    if user_repository.get_by_email(db, payload.email) is not None:
        raise AuthError("email already registered", status_code=400)
    return user_repository.create(
        db,
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )


def authenticate(db: Session, email: str, password: str) -> User:
    user = user_repository.get_by_email(db, email)
    if user is None or user.hashed_password is None:
        raise AuthError("invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise AuthError("invalid credentials")
    if not user.is_active:
        raise AuthError("account disabled", status_code=403)
    return user


def _role_and_perms(user: User) -> tuple[str | None, list[str]]:
    if user.role is None:
        return None, []
    return user.role.name, [p.name for p in user.role.permissions]


def issue_token_pair(db: Session, user: User) -> TokenPair:
    jti = uuid.uuid4().hex
    refresh, expires_at = create_refresh_token(str(user.id), jti)
    refresh_token_repository.create(db, user_id=user.id, jti=jti, expires_at=expires_at)
    role, perms = _role_and_perms(user)
    access = create_access_token(str(user.id), role=role, perms=perms)
    return TokenPair(access_token=access, refresh_token=refresh)


def refresh_access(db: Session, refresh_token: str) -> AccessToken:
    try:
        claims = decode_token(refresh_token)
    except TokenError as e:
        raise AuthError(f"invalid refresh token: {e}") from e
    if claims.get("type") != "refresh":
        raise AuthError("invalid refresh token")
    jti = claims.get("jti")
    sub = claims.get("sub")
    if not jti or not sub:
        raise AuthError("invalid refresh token")
    if refresh_token_repository.get_active(db, jti) is None:
        raise AuthError("refresh token revoked or expired")
    role: str | None = None
    perms: list[str] = []
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        user_id = None
    if user_id is not None:
        user = user_repository.get(db, user_id)
        if user is not None:
            role, perms = _role_and_perms(user)
    return AccessToken(access_token=create_access_token(sub, role=role, perms=perms))


def revoke(db: Session, refresh_token: str) -> None:
    try:
        claims = decode_token(refresh_token)
    except TokenError:
        return
    jti = claims.get("jti")
    if jti:
        refresh_token_repository.revoke(db, jti)


def login_or_create_from_oauth(
    db: Session,
    *,
    provider: str,
    provider_account_id: str,
    email: str,
    name: str,
) -> User:
    account = oauth_repository.get_by_provider(db, provider, provider_account_id)
    if account is not None:
        user = user_repository.get(db, account.user_id)
        if user is None:
            raise AuthError("linked user missing", status_code=500)
        return user

    user = user_repository.get_by_email(db, email)
    if user is None:
        user = user_repository.create(db, email=email, name=name, hashed_password=None)
    oauth_repository.link(
        db,
        user_id=user.id,
        provider=provider,
        provider_account_id=provider_account_id,
    )
    return user
