# ── Relay-med Dev Startup ─────────────────────────────────────────────────────
# Run this from the project root to start both backend and frontend together.
# Usage: Right-click > "Run with PowerShell"  OR  pwsh .\start_dev.ps1

$root = $PSScriptRoot

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        Relay-med Dev Startup Script          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 1. Start Backend ──────────────────────────────────────────────────────────
Write-Host "▶ Starting backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root'; Write-Host '[BACKEND] Starting uvicorn...' -ForegroundColor Green; uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
)

Start-Sleep -Seconds 2

# ── 2. Start Frontend ─────────────────────────────────────────────────────────
$frontendDir = Join-Path $root "relay-med-frontend (1)"
Write-Host "▶ Starting frontend (Vite) in $frontendDir ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendDir'; Write-Host '[FRONTEND] Starting Vite...' -ForegroundColor Yellow; npm run dev"
)

Write-Host ""
Write-Host "✅ Both servers launched in separate windows." -ForegroundColor Cyan
Write-Host "   Backend  → http://localhost:8000" -ForegroundColor Green
Write-Host "   Frontend → http://localhost:3000  (or the port Vite chooses)" -ForegroundColor Yellow
Write-Host ""
Write-Host "   API Docs → http://localhost:8000/api/docs" -ForegroundColor Gray
Write-Host ""
