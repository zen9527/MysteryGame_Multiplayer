# Script Murder - Start Servers
$SCRIPT_DIR = $PSScriptRoot
Set-Location $SCRIPT_DIR

Write-Host "=== Starting Script Murder ===" -ForegroundColor Cyan

# Check environment
python --version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Python not found"; exit 1 }
node --version 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: Node.js not found"; exit 1 }

# Install dependencies if needed
if (!(Test-Path "client\node_modules")) { Write-Host "Installing frontend..."; Set-Location client; npm install --silent; Set-Location .. }
pip show fastapi --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "Installing backend..."; pip install -r requirements.txt --quiet }

# Create .env if needed
if (!(Test-Path ".env") -and (Test-Path ".env.example")) { Copy-Item .env.example .env; Write-Host "Created .env" }

# Start servers
Write-Host "Starting backend (8000)..." -ForegroundColor Green
Start-Process powershell "-NoExit -Command cd '$SCRIPT_DIR'; uvicorn server.main:app --host 0.0.0.0 --port 8000"
Start-Sleep 1

Write-Host "Starting frontend (3000)..." -ForegroundColor Green
Start-Process powershell "-NoExit -Command cd '$SCRIPT_DIR\client'; npm run dev"

Write-Host "`nServers started!`n  Backend: http://localhost:8000`n  Frontend: http://localhost:3000`n  Stop: .\stop.ps1" -ForegroundColor Yellow
