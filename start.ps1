# Script Murder - Start Servers
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Starting Script Murder ===" -ForegroundColor Cyan

# Check dependencies
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
python --version >$null 2>&1 || { Write-Host "ERROR: Python not found" -ForegroundColor Red; Read-Host; exit 1 }
Write-Host "  OK" -ForegroundColor Green

Write-Host "[2/4] Checking Node.js..." -ForegroundColor Yellow
node --version >$null 2>&1 || { Write-Host "ERROR: Node.js not found" -ForegroundColor Red; Read-Host; exit 1 }
Write-Host "  OK" -ForegroundColor Green

# Install dependencies if needed
if (!(Test-Path "$scriptDir\client\node_modules")) {
    Write-Host "[3/4] Installing frontend..." -ForegroundColor Yellow
    Push-Location "$scriptDir\client"; npm install; Pop-Location
}
pip show fastapi >$null 2>&1 || { Write-Host "[3/4] Installing backend..." -ForegroundColor Yellow; pip install -r "$scriptDir\requirements.txt" }

# Create .env if missing
if (!(Test-Path "$scriptDir\.env") -and (Test-Path "$scriptDir\.env.example")) {
    Copy-Item "$scriptDir\.env.example" "$scriptDir\.env"
    Write-Host "[4/4] Created .env" -ForegroundColor Green
} else { Write-Host "[4/4] Config OK" -ForegroundColor Green }

# Start servers
Write-Host ""
Write-Host "Starting backend (8000)..." -ForegroundColor Cyan
Start-Process powershell -Args "-NoExit","-Command","cd '$scriptDir'; uvicorn server.main:app --host 0.0.0.0 --port 8000"
Start-Sleep 2
Write-Host "Starting frontend (3000)..." -ForegroundColor Cyan
Start-Process powershell -Args "-NoExit","-Command","cd '$scriptDir\client'; npm run dev"

Write-Host ""
Write-Host "=== Servers Started ===" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Frontend: http://localhost:3000"
Write-Host ""
Read-Host "Press Enter to close"
