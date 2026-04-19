from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.oauth import oauth
from ...schemas.auth import (
    AccessToken,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from ...schemas.user import UserRead
from ...services import auth_service
from ...services.auth_service import AuthError
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _raise(err: AuthError) -> None:
    raise HTTPException(status_code=err.status_code, detail=err.message)


@router.post("/register", response_model=TokenPair, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        user = auth_service.register(db, payload)
    except AuthError as e:
        _raise(e)
    return auth_service.issue_token_pair(db, user)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        user = auth_service.authenticate(db, payload.email, payload.password)
    except AuthError as e:
        _raise(e)
    return auth_service.issue_token_pair(db, user)


@router.post("/refresh", response_model=AccessToken)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessToken:
    try:
        return auth_service.refresh_access(db, payload.refresh_token)
    except AuthError as e:
        _raise(e)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    auth_service.revoke(db, payload.refresh_token)


@router.get("/me", response_model=UserRead)
def me(user=Depends(get_current_user)) -> UserRead:
    role_name = user.role.name if user.role is not None else None
    perms = [p.name for p in user.role.permissions] if user.role is not None else []
    return UserRead(
        id=user.id,
        email=user.email,
        name=user.name,
        role=role_name,
        permissions=perms,
    )


def _require_client(provider: str):
    client = getattr(oauth, provider, None)
    if client is None:
        raise HTTPException(status_code=503, detail=f"{provider} oauth not configured")
    return client


@router.get("/google/login")
async def google_login(request: Request):
    client = _require_client("google")
    redirect_uri = f"{settings.oauth_redirect_base}/auth/google/callback"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", response_model=TokenPair)
async def google_callback(request: Request, db: Session = Depends(get_db)) -> TokenPair:
    client = _require_client("google")
    token = await client.authorize_access_token(request)
    info = token.get("userinfo") or await client.userinfo(token=token)
    sub = info.get("sub")
    email = info.get("email")
    name = info.get("name") or (email.split("@")[0] if email else "user")
    if not sub or not email:
        raise HTTPException(status_code=400, detail="google returned no identity")
    try:
        user = auth_service.login_or_create_from_oauth(
            db, provider="google", provider_account_id=str(sub), email=email, name=name
        )
    except AuthError as e:
        _raise(e)
    return auth_service.issue_token_pair(db, user)


@router.get("/github/login")
async def github_login(request: Request):
    client = _require_client("github")
    redirect_uri = f"{settings.oauth_redirect_base}/auth/github/callback"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/github/callback", response_model=TokenPair)
async def github_callback(request: Request, db: Session = Depends(get_db)) -> TokenPair:
    client = _require_client("github")
    token = await client.authorize_access_token(request)
    profile = (await client.get("user", token=token)).json()
    gh_id = profile.get("id")
    name = profile.get("name") or profile.get("login") or "user"
    email = profile.get("email")
    if not email:
        emails = (await client.get("user/emails", token=token)).json()
        primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
        email = primary["email"] if primary else None
    if not gh_id or not email:
        raise HTTPException(status_code=400, detail="github returned no identity")
    try:
        user = auth_service.login_or_create_from_oauth(
            db, provider="github", provider_account_id=str(gh_id), email=email, name=name
        )
    except AuthError as e:
        _raise(e)
    return auth_service.issue_token_pair(db, user)
