"""
Relay-med AI Health Companion — FastAPI Application Entry Point
Mounts all v1 routes, configures CORS, and logs startup event.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import settings
from backend.api.v1.routes import ingest, consent, reports, conversation, audit, feedback, bias
from backend.services.audit_logger import audit_logger, AuditEventType

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Trust-aware AI health companion with causal inference, "
        "differential privacy, and hospital-grade security."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow all origins in dev, restrict in production via CORS_ORIGINS env var
cors_origins = settings.CORS_ORIGINS
if cors_origins == "*":
    origins_list = ["*"]
else:
    origins_list = [o.strip() for o in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ────────────────────────────────────────────────────────────────
app.include_router(ingest.router, prefix=settings.API_V1_STR)
app.include_router(consent.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(conversation.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(feedback.router, prefix=settings.API_V1_STR)
app.include_router(bias.router, prefix=settings.API_V1_STR)

# ── Static Frontend (only if frontend dir exists — not used in Render deploy) ─
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    provider = settings.effective_provider
    audit_logger.log(
        AuditEventType.SYSTEM_STARTUP,
        {"llm_provider": provider, "version": "1.0.0"},
    )
    print(f"{settings.APP_NAME} started -- LLM: {provider.upper()}")
    if provider == "fallback":
        print("  (No API key configured -- using built-in health knowledge base)")

# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "llm_provider": settings.effective_provider,
    }
