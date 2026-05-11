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
    RELAYMED_MASTER_KEY: str = "dev_master_key_32_bytes_long_minimum"
    
    # Data Trust
    STALENESS_THRESHOLD_DAYS: int = 7
    TRUST_WEIGHT_SOURCE: float = 0.5
    TRUST_WEIGHT_COMPLETENESS: float = 0.3
    TRUST_WEIGHT_RECENCY: float = 0.2
    
    # Emergency Triage Thresholds
    SPO2_RED_FLAG_THRESHOLD: float = 90.0
    CHEST_PAIN_RED_FLAG_THRESHOLD: int = 7  # On a scale of 1-10
    
    # Database
    DATABASE_URL: str = "sqlite:///./securemed.db"

    # CORS — allowed frontend origins
    CORS_ORIGINS: str = "http://localhost:8080,http://127.0.0.1:8080"

    @property
    def effective_provider(self) -> str:
        """Auto-detect: if gemini is chosen but no API key, fall back gracefully."""
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            return "fallback"
        return self.LLM_PROVIDER

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
