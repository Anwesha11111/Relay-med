import os
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "Relay-med AI Health Companion"
    API_V1_STR: str = "/api/v1"
    
    # LLM Configuration
    # Options: "ollama" | "gemini" | "fallback"
    LLM_PROVIDER: Literal["ollama", "gemini", "fallback"] = "gemini"
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:latest"
    
    # Security
    SECUREMED_MASTER_KEY: str = "dev_master_key_32_bytes_long_minimum"

    # ── Authentication ──────────────────────────────────────────────────────────
    # AUTH_MODE controls how get_current_user_id() resolves identity:
    #   "header" (default/dev) — trusts X-User-ID header, falls back to "default"
    #   "jwt"                  — requires Authorization: Bearer <HS256 JWT>
    AUTH_MODE: Literal["header", "jwt"] = "header"
    # HS256 signing secret for app-issued session tokens.
    # Falls back to SECUREMED_MASTER_KEY when blank (fine for dev, set in prod).
    SECUREMED_JWT_SECRET: str = ""
    # Access-token lifetime in minutes (default 7 days).
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    # Google OAuth Web Client ID — enables "Continue with Google".
    # Create one at https://console.cloud.google.com/apis/credentials
    GOOGLE_CLIENT_ID: str = "311664875682-qckafchjiual8k169u8tmnicm13t8s6d.apps.googleusercontent.com"
    
    # Data Trust — weights must sum to 1.0.
    # Recency carries 0.4 so that data older than STALENESS_THRESHOLD_DAYS is
    # meaningfully distrusted: a fully-reliable, complete record still drops to
    # ~0.6 once stale (recency→0), rather than bottoming out at 0.8.
    STALENESS_THRESHOLD_DAYS: int = 7
    TRUST_WEIGHT_SOURCE: float = 0.4
    TRUST_WEIGHT_COMPLETENESS: float = 0.2
    TRUST_WEIGHT_RECENCY: float = 0.4
    
    # Emergency Triage Thresholds
    SPO2_RED_FLAG_THRESHOLD: float = 90.0
    CHEST_PAIN_RED_FLAG_THRESHOLD: int = 7  # On a scale of 1-10
    
    # Database
    DATABASE_URL: str = "sqlite:///./securemed.db"

    # CORS — allowed frontend origins
    CORS_ORIGINS: str = "*"

    @property
    def jwt_secret(self) -> str:
        """Signing secret for session tokens; falls back to the master key in dev."""
        return self.SECUREMED_JWT_SECRET or self.SECUREMED_MASTER_KEY

    @property
    def effective_provider(self) -> str:
        """Auto-detect: if gemini is chosen but no API key, fall back gracefully."""
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            return "fallback"
        return self.LLM_PROVIDER

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
