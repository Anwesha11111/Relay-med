"""
Auth Routes — real account + session management.

  POST /api/v1/auth/register   email/password signup           -> { token, user }
  POST /api/v1/auth/login      email/password login            -> { token, user }
  POST /api/v1/auth/google     verify Google credential, login -> { token, user }
  GET  /api/v1/auth/me         current user (Bearer required)   -> { user }
  POST /api/v1/auth/logout     audit + client drops token       -> { ok }

Session tokens are HS256 JWTs issued by auth_service. Clients send them as
`Authorization: Bearer <token>` on subsequent requests.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.services.auth_service import (
    auth_service,
    create_access_token,
    decode_access_token,
    verify_google_id_token,
    TokenError,
    User,
)
from backend.services.audit_logger import audit_logger, AuditEventType
from backend.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Schemas ──────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=200)
    name: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class GoogleRequest(BaseModel):
    credential: str = Field(min_length=1, description="Google Identity Services ID token")


# ── Current-user dependency ──────────────────────────────────────────────────
def current_user(authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = auth_service.get_by_id(payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user.")
    return user


def _token_response(user: User) -> dict:
    return {"token": create_access_token(user.id, {"email": user.email}), "user": user.public()}


# ── Routes ───────────────────────────────────────────────────────────────────
@router.post("/register")
async def register(payload: RegisterRequest):
    try:
        user = auth_service.register(payload.email, payload.password, payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    audit_logger.log(AuditEventType.AUTH_SUCCESS, {"action": "register", "provider": "email"}, user_id=user.id)
    return _token_response(user)


@router.post("/login")
async def login(payload: LoginRequest):
    user = auth_service.authenticate(payload.email, payload.password)
    if not user:
        audit_logger.log(
            AuditEventType.AUTH_FAILURE, {"action": "login", "email": payload.email.lower()}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
        )
    audit_logger.log(AuditEventType.AUTH_SUCCESS, {"action": "login", "provider": "email"}, user_id=user.id)
    return _token_response(user)


@router.post("/google")
async def google_login(payload: GoogleRequest):
    try:
        claims = await verify_google_id_token(payload.credential)
    except TokenError as exc:
        audit_logger.log(AuditEventType.AUTH_FAILURE, {"action": "google", "reason": str(exc)})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = auth_service.get_or_create_oauth(
        provider="google",
        email=claims.get("email", ""),
        name=claims.get("name", ""),
        picture=claims.get("picture"),
    )
    audit_logger.log(AuditEventType.AUTH_SUCCESS, {"action": "login", "provider": "google"}, user_id=user.id)
    return _token_response(user)


@router.get("/me")
async def me(user: User = Depends(current_user)):
    return {"user": user.public()}


@router.post("/logout")
async def logout(user: User = Depends(current_user)):
    # Stateless JWTs: the client discards the token. We record the event for audit.
    audit_logger.log(AuditEventType.AUTH_SUCCESS, {"action": "logout"}, user_id=user.id)
    return {"ok": True}


@router.get("/config")
async def auth_config():
    """Public bootstrap info so the frontend knows which providers are enabled."""
    return {
        "google_enabled": bool(settings.GOOGLE_CLIENT_ID),
        "google_client_id": settings.GOOGLE_CLIENT_ID or None,
    }
