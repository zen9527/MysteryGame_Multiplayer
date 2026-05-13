# Script Murder - Start Servers
# PowerShell version for better reliability

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Start Script Murder ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  [OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node.js
Write-Host "[2/6] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  [OK] $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Node.js not installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install frontend dependencies if needed
Write-Host "[3/6] Checking frontend dependencies..." -ForegroundColor Yellow
if (!(Test-Path "$scriptDir\client\node_modules")) {
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location "$scriptDir\client"
    npm install
    Pop-Location
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Frontend installation failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "  [OK] Frontend dependencies exist" -ForegroundColor Green
}

# Install backend dependencies if needed
Write-Host "[4/6] Checking backend dependencies..." -ForegroundColor Yellow
try {
    pip show fastapi --quiet 2>&1 | Out-Null
    Write-Host "  [OK] Backend dependencies exist" -ForegroundColor Green
} catch {
    Write-Host "  Installing backend dependencies..." -ForegroundColor Yellow
    Push-Location $scriptDir
    pip install -r requirements.txt
    Pop-Location
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Backend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Backend installation failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Create .env if missing
Write-Host "[5/6] Checking config file..." -ForegroundColor Yellow
if (!(Test-Path "$scriptDir\.env")) {
    if (Test-Path "$scriptDir\.env.example") {
        Copy-Item "$scriptDir\.env.example" "$scriptDir\.env"
        Write-Host "  [OK] Created .env file" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] No .env.example, please create .env manually" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [OK] .env file exists" -ForegroundColor Green
}

# Start servers
Write-Host "[6/6] Starting servers..." -ForegroundColor Yellow
Write-Host ""

Write-Host "Starting backend (port 8000)..." -ForegroundColor Cyan
$backendArgs = @("-NoExit", "-Command", "cd '$scriptDir'; uvicorn server.main:app --host 0.0.0.0 --port 8000")
Start-Process powershell -ArgumentList $backendArgs -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "Starting frontend (port 3000)..." -ForegroundColor Cyan
$frontendArgs = @("-NoExit", "-Command", "cd '$scriptDir\client'; npm run dev")
Start-Process powershell -ArgumentList $frontendArgs -WindowStyle Normal

Write-Host ""
Write-Host "=== Servers Started ===" -ForegroundColor Green
Write-Host "  Backend: http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Tips:" -ForegroundColor Cyan
Write-Host "  - Backend and frontend run in new windows" -ForegroundColor Gray
Write-Host "  - Close those windows to stop servers" -ForegroundColor Gray
Write-Host "  - Or use stop.bat to stop all services" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to close this window"
