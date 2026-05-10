"""
dependencies.py — FastAPI dependency-injection helpers.

Provides
--------
get_current_user_id
    Extracts user identity from either:
      • X-User-ID header  (AUTH_MODE="header", default / dev)
      • Bearer JWT        (AUTH_MODE="jwt",    production)

require_consent(stream_id)
    Raises HTTP 403 if the user hasn't granted consent for a data stream.

RateLimiter
    Per-user sliding-window rate limiter (in-process, single-worker safe).
    Pre-built instances: ingest_rate_limit, chat_rate_limit, reports_rate_limit.

require_role(role)
    Minimal RBAC guard; roles are embedded in JWT claims or set via assign_role().

Auth modes
----------
Set AUTH_MODE in .env:
  "header"  (default) — trusts X-User-ID request header; falls back to "default".
  "jwt"               — expects Authorization: Bearer <HS256 JWT>.
                        Requires RELAYMED_JWT_SECRET in .env.
                        Install: pip install python-jose[cryptography]
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from backend.config import settings
from backend.services.consent_manager import consent_manager


# ── User Identity ──────────────────────────────────────────────────────────────


def _extract_user_header(
    x_user_id: str | None = Header(default=None),
) -> str:
    """
    Header-mode auth.
    Reads the X-User-ID header; returns "default" when absent.
    Safe for local development — no credentials required.
    """
    return (x_user_id or "").strip() or "default"


def _extract_user_jwt(
    authorization: str | None = Header(default=None),
) -> str:
    """
    JWT-mode auth.
    Reads Authorization: Bearer <token>, decodes with RELAYMED_JWT_SECRET (HS256),
    and returns the 'sub' claim as the user_id.
    """
    try:
        from jose import JWTError, jwt  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "JWT auth requires 'python-jose[cryptography]'. "
            "Run: pip install 'python-jose[cryptography]'"
        ) from exc

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ").strip()
    secret = getattr(settings, "RELAYMED_JWT_SECRET", "")

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RELAYMED_JWT_SECRET is not configured on the server.",
        )

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT payload is missing the 'sub' claim.",
        )

    return user_id


def get_current_user_id(
    x_user_id: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> str:
    """
    Unified user-identity dependency.
    Delegates to header or JWT mode based on settings.AUTH_MODE.
    """
    mode = getattr(settings, "AUTH_MODE", "header")
    if mode == "jwt":
        return _extract_user_jwt(authorization)
    return _extract_user_header(x_user_id)


# Convenience type alias — use in route signatures:
#   async def my_route(user_id: CurrentUser): ...
CurrentUser = Annotated[str, Depends(get_current_user_id)]


# ── Consent Guard ──────────────────────────────────────────────────────────────


def require_consent(stream_id: str):
    """
    Returns a FastAPI Depends() that raises HTTP 403 when the current user
    has not granted consent for *stream_id*.

    Usage
    -----
        @router.post("/ingest")
        async def ingest(
            record: IngestRequest,
            user_id: CurrentUser,
            _: None = require_consent("manual_input"),
        ): ...
    """

    def _check(user_id: CurrentUser) -> None:
        if not consent_manager.check_consent(user_id, stream_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Consent for data stream '{stream_id}' has not been granted. "
                    f"Enable it in the Consent Manager before submitting data."
                ),
            )

    return Depends(_check)


# ── Rate Limiter ───────────────────────────────────────────────────────────────


class _SlidingWindowCounter:
    """
    In-process sliding-window counter.
    Thread-unsafe; adequate for single-worker development.
    Replace with Redis + lua script for multi-worker production.
    """

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window = window_seconds
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._buckets[key]
        cutoff = now - self.window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        cutoff = now - self.window
        active = sum(1 for ts in self._buckets[key] if ts >= cutoff)
        return max(0, self.limit - active)


# One counter per logical endpoint group
_ingest_counter  = _SlidingWindowCounter(limit=120, window_seconds=60)
_chat_counter    = _SlidingWindowCounter(limit=30,  window_seconds=60)
_reports_counter = _SlidingWindowCounter(limit=60,  window_seconds=60)


class RateLimiter:
    """
    FastAPI dependency that enforces per-user rate limits.

    Usage
    -----
        _chat_limiter = RateLimiter(_chat_counter)

        @router.post("/chat")
        async def chat(
            user_id: CurrentUser,
            _: None = Depends(_chat_limiter),
        ): ...
    """

    def __init__(self, counter: _SlidingWindowCounter) -> None:
        self._counter = counter

    def __call__(self, user_id: CurrentUser) -> None:
        if not self._counter.is_allowed(user_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded: max {self._counter.limit} requests "
                    f"per {self._counter.window}s."
                ),
                headers={"Retry-After": str(self._counter.window)},
            )


# Pre-built Depends() instances — import directly into route files
ingest_rate_limit  = Depends(RateLimiter(_ingest_counter))
chat_rate_limit    = Depends(RateLimiter(_chat_counter))
reports_rate_limit = Depends(RateLimiter(_reports_counter))


# ── RBAC ───────────────────────────────────────────────────────────────────────
# Minimal in-process role store.
# In production: embed roles in JWT claims or load from a DB at login.

ROLE_ADMIN  = "admin"
ROLE_VIEWER = "viewer"

_role_store: dict[str, set[str]] = {}


def assign_role(user_id: str, role: str) -> None:
    """Assign *role* to *user_id* (persists only until process restart)."""
    _role_store.setdefault(user_id, set()).add(role)


def get_roles(user_id: str) -> set[str]:
    """Return the set of roles held by *user_id*. Defaults to {viewer}."""
    return _role_store.get(user_id, {ROLE_VIEWER})


def require_role(role: str):
    """
    Returns a FastAPI Depends() that raises HTTP 403 unless the user holds *role*.

    Usage
    -----
        @router.delete("/audit/purge")
        async def purge(
            user_id: CurrentUser,
            _: None = require_role(ROLE_ADMIN),
        ): ...
    """

    def _check(user_id: CurrentUser) -> None:
        if role not in get_roles(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is required for this operation.",
            )

    return Depends(_check)
