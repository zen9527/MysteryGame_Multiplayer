# Script Murder - Unified Startup Script
$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
$PIDS_DIR = Join-Path $SCRIPT_DIR ".pids"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script Murder - Starting Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create PID directory
if (!(Test-Path $PIDS_DIR)) { New-Item -ItemType Directory -Path $PIDS_DIR | Out-Null }

# Switch to script directory
Set-Location $SCRIPT_DIR

# Check environment
Write-Host "[1/4] Checking environment..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK: Python $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Python not found" -ForegroundColor Red
    exit 1
}

$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK: Node.js $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Node.js not found" -ForegroundColor Red
    exit 1
}

# Check dependencies
Write-Host "[2/4] Checking dependencies..." -ForegroundColor Yellow
if (!(Test-Path "client\node_modules")) {
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location client
    npm install
    Set-Location ..
}
pip show fastapi --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Installing backend dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet
}
Write-Host "  OK: Dependencies checked" -ForegroundColor Green

# Check configuration
Write-Host "[3/4] Checking configuration..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "  OK: Created .env from template" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: No .env file found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  OK: .env exists" -ForegroundColor Green
}

# Start servers
Write-Host "[4/4] Starting servers..." -ForegroundColor Yellow

# Backend
$backendCmd = "cd '$SCRIPT_DIR'; uvicorn server.main:app --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal
Start-Sleep -Seconds 1

# Frontend
$frontendCmd = "cd '$SCRIPT_DIR\client'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Servers started successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "  Stop servers: run stop.ps1" -ForegroundColor Yellow
Write-Host ""
