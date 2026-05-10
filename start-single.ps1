# Script Murder - Single Window Mode
$ErrorActionPreference = "Continue"
$SCRIPT_DIR = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script Murder - Single Window Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Yellow
Write-Host ""

Set-Location $SCRIPT_DIR

# Check environment
Write-Host "[Check] Python and Node.js..." -ForegroundColor Yellow
python --version 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "  OK: Python" -ForegroundColor Green } else { Write-Host "  ERROR: Python missing"; exit 1 }
node --version 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "  OK: Node.js" -ForegroundColor Green } else { Write-Host "  ERROR: Node.js missing"; exit 1 }

# Check dependencies
if (!(Test-Path "client\node_modules")) {
    Write-Host "[Install] Frontend dependencies..." -ForegroundColor Yellow
    Set-Location client; npm install; Set-Location ..
}
pip show fastapi --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Install] Backend dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet
}

# Check configuration
if (!(Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item .env.example .env
    Write-Host "[Note] Please check LLM_ENDPOINT in .env" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Starting servers (Ctrl+C to stop)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Start backend as background job
$backendJob = Start-Job -ScriptBlock {
    Write-Host "=== Backend (8000) ===" -ForegroundColor Cyan
    Set-Location $using:SCRIPT_DIR
    uvicorn server.main:app --host 0.0.0.0 --port 8000
}

Start-Sleep -Seconds 2

# Run frontend in foreground
Write-Host "=== Frontend (3000) ===" -ForegroundColor Magenta
Set-Location client
npm run dev

# Cleanup
Stop-Job $backendJob
Remove-Job $backendJob
