"""
Auth Service — Real user authentication for Relay-med.

Provides
--------
- Email/password accounts (PBKDF2-HMAC-SHA256 hashing, no plaintext stored)
- OAuth accounts (Google) — verified server-side, then linked to a local user
- App session tokens (HS256 JWT, signed with settings.jwt_secret)

Zero third-party dependencies: JWT and password hashing are implemented with the
Python standard library (hmac / hashlib / secrets / base64), so this runs anywhere
the rest of the backend runs — no python-jose / passlib / bcrypt required.

Persistence mirrors ConsentManager: a thread-locked JSON file on disk.
Swap the store for a real DB (DATABASE_URL is already configured) before scaling
past a single worker.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from backend.config import settings

DATA_PATH = Path("./data/auth/users.json")

# PBKDF2 parameters
_PBKDF2_ALGO = "sha256"
_PBKDF2_ITERATIONS = 200_000
_SALT_BYTES = 16


# ── Base64URL helpers (JWT uses unpadded base64url) ──────────────────────────
def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


# ── Password hashing (stdlib PBKDF2) ─────────────────────────────────────────
def hash_password(password: str) -> str:
    """Return 'pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>'."""
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_{_PBKDF2_ALGO}${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verification against a stored hash string."""
    try:
        scheme, iterations, salt_hex, hash_hex = stored.split("$")
        assert scheme == f"pbkdf2_{_PBKDF2_ALGO}"
        dk = hashlib.pbkdf2_hmac(
            _PBKDF2_ALGO, password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# ── JWT (HS256, stdlib) ──────────────────────────────────────────────────────
class TokenError(Exception):
    """Raised when a session token is missing, malformed, or expired."""


def create_access_token(sub: str, extra: Optional[Dict[str, Any]] = None) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload: Dict[str, Any] = {
        "sub": sub,
        "iat": now,
        "exp": now + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    if extra:
        payload.update(extra)
    segments = [
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    segments.append(_b64url_encode(signature))
    return ".".join(segments)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise TokenError("Malformed token") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected = hmac.new(settings.jwt_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
        raise TokenError("Invalid signature")

    payload = json.loads(_b64url_decode(payload_b64))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise TokenError("Token expired")
    return payload


# ── User model ───────────────────────────────────────────────────────────────
@dataclass
class User:
    id: str
    email: str
    name: str
    provider: str  # "email" | "google" | "twitter"
    avatar: str  # single-letter initial for the UI
    created_at: str
    password_hash: Optional[str] = None
    picture: Optional[str] = None

    def public(self) -> Dict[str, Any]:
        """User shape safe to send to the client (never includes the hash)."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "provider": self.provider,
            "avatar": self.avatar,
            "picture": self.picture,
            "joined": self.created_at,
        }


def _initial(name: str, email: str) -> str:
    base = (name or email or "U").strip()
    return base[0].upper() if base else "U"


# ── User store (thread-locked JSON, mirrors ConsentManager) ──────────────────
class AuthService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._users: Dict[str, User] = {}
        self._email_index: Dict[str, str] = {}  # lowercased email -> user id
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    # — registration / login —
    def register(self, email: str, password: str, name: str = "") -> User:
        email_norm = email.strip().lower()
        if not email_norm or "@" not in email_norm:
            raise ValueError("A valid email address is required.")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        with self._lock:
            if email_norm in self._email_index:
                raise ValueError("An account with this email already exists.")
            user = User(
                id=f"user_{uuid.uuid4().hex[:12]}",
                email=email_norm,
                name=name.strip() or email_norm.split("@")[0],
                provider="email",
                avatar=_initial(name, email_norm),
                created_at=datetime.now(timezone.utc).isoformat(),
                password_hash=hash_password(password),
            )
            self._put(user)
            self._save()
        return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if user and user.password_hash and verify_password(password, user.password_hash):
            return user
        return None

    def get_or_create_oauth(
        self, provider: str, email: str, name: str, picture: Optional[str] = None
    ) -> User:
        email_norm = email.strip().lower()
        existing = self.get_by_email(email_norm)
        if existing:
            # Keep profile fresh; never downgrade an existing email account's provider.
            with self._lock:
                if picture:
                    existing.picture = picture
                self._save()
            return existing
        with self._lock:
            user = User(
                id=f"{provider}_{uuid.uuid4().hex[:12]}",
                email=email_norm,
                name=name.strip() or email_norm.split("@")[0],
                provider=provider,
                avatar=_initial(name, email_norm),
                created_at=datetime.now(timezone.utc).isoformat(),
                picture=picture,
            )
            self._put(user)
            self._save()
        return user

    # — lookups —
    def get_by_id(self, user_id: str) -> Optional[User]:
        with self._lock:
            return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        with self._lock:
            uid = self._email_index.get(email.strip().lower())
            return self._users.get(uid) if uid else None

    # — internals —
    def _put(self, user: User) -> None:
        self._users[user.id] = user
        self._email_index[user.email] = user.id

    def _save(self) -> None:
        data = {uid: asdict(u) for uid, u in self._users.items()}
        tmp = DATA_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(DATA_PATH)  # atomic on the same filesystem

    def _load(self) -> None:
        if not DATA_PATH.exists():
            return
        try:
            data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            for uid, v in data.items():
                user = User(**v)
                self._users[uid] = user
                self._email_index[user.email] = uid
        except Exception:
            pass  # start empty on a corrupt store rather than crash


# ── Google ID-token verification (no extra deps — uses Google's tokeninfo) ───
async def verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """
    Verify a Google Identity Services credential server-side and return its claims.
    Raises TokenError if the token is invalid or not issued for our client ID.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise TokenError("Google sign-in is not configured (GOOGLE_CLIENT_ID is unset).")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token}
            )
    except Exception as exc:
        raise TokenError(f"Could not reach Google to verify the token: {exc}") from exc

    if resp.status_code != 200:
        raise TokenError("Google rejected the credential.")
    claims = resp.json()

    if claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise TokenError("Google token was issued for a different application.")
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise TokenError("Unexpected token issuer.")
    if claims.get("email_verified") not in (True, "true"):
        raise TokenError("Google account email is not verified.")
    return claims


# Singleton
auth_service = AuthService()
