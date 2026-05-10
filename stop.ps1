# Script Murder - Unified Stop Script
$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script Murder - Stopping Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop backend (port 8000)
Write-Host "Checking backend process (port 8000)..." -ForegroundColor Yellow
$backendProcesses = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($backendProcesses) {
    foreach ($processId in $backendProcesses) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Write-Host "  Stopped backend PID=$processId" -ForegroundColor Green
    }
} else {
    Write-Host "  Backend not running" -ForegroundColor Gray
}

# Stop frontend (port 3000)
Write-Host "Checking frontend process (port 3000)..." -ForegroundColor Yellow
$frontendProcesses = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($frontendProcesses) {
    foreach ($processId in $frontendProcesses) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Write-Host "  Stopped frontend PID=$processId" -ForegroundColor Green
    }
} else {
    Write-Host "  Frontend not running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Servers stopped" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
