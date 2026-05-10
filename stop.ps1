# Script Murder - Unified Stop Script
# PowerShell 版本：通过端口检测进程，更可靠

$ErrorActionPreference = "Continue"
$PIDS_DIR = ".pids"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script Murder - 停止服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 清理后端进程（端口 8000）
Write-Host "检查后端进程 (端口 8000)..." -ForegroundColor Yellow
$backendProcesses = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($backendProcesses) {
    foreach ($pid in $backendProcesses) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ 已停止后端进程 PID=$pid" -ForegroundColor Green
    }
} else {
    Write-Host "  ℹ 后端未运行" -ForegroundColor Gray
}

# 清理前端进程（端口 3000）
Write-Host "检查前端进程 (端口 3000)..." -ForegroundColor Yellow
$frontendProcesses = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($frontendProcesses) {
    foreach ($pid in $frontendProcesses) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ 已停止前端进程 PID=$pid" -ForegroundColor Green
    }
} else {
    Write-Host "  ℹ 前端未运行" -ForegroundColor Gray
}

# 清理日志文件
if (Test-Path $PIDS_DIR) {
    Remove-Item "$PIDS_DIR\*.log" -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ 服务器已停止" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
