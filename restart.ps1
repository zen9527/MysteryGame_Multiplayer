# Script Murder - Restart Script
$SCRIPT_DIR = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script Murder - Restarting Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Stopping existing servers..." -ForegroundColor Yellow
& "$SCRIPT_DIR\stop.ps1"

Write-Host ""
Write-Host "Step 2: Waiting 2 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Step 3: Starting new servers..." -ForegroundColor Yellow
& "$SCRIPT_DIR\start.ps1"
