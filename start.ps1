# Script Murder - Unified Startup Script
# PowerShell 版本：更简洁、更可靠

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
$PIDS_DIR = Join-Path $SCRIPT_DIR ".pids"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script Murder - 启动服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 创建 PID 目录
if (!(Test-Path $PIDS_DIR)) { New-Item -ItemType Directory -Path $PIDS_DIR | Out-Null }

# 切换到脚本目录
Set-Location $SCRIPT_DIR

# 检查环境
Write-Host "[1/4] 检查环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python 未安装" -ForegroundColor Red
    exit 1
}

try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js: v$nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js 未安装" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host "[2/4] 检查依赖..." -ForegroundColor Yellow
if (!(Test-Path "client\node_modules")) {
    Write-Host "  安装前端依赖..." -ForegroundColor Yellow
    Set-Location client
    npm install --silent
    Set-Location ..
}
try {
    pip show fastapi --quiet 2>&1 | Out-Null
    Write-Host "  ✓ 后端依赖已安装" -ForegroundColor Green
} catch {
    Write-Host "  安装后端依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet
}

# 检查配置
Write-Host "[3/4] 检查配置..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "  ✓ 已创建 .env（请检查 LLM_ENDPOINT 配置）" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ 警告：未找到 .env 文件" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ .env 配置存在" -ForegroundColor Green
}

# 启动服务器
Write-Host "[4/4] 启动服务器..." -ForegroundColor Yellow

# 后端
$backendLog = Join-Path $PIDS_DIR "backend.log"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$SCRIPT_DIR'; Write-Host '=== Backend Server ===' -ForegroundColor Cyan; uvicorn server.main:app --host 0.0.0.0 --port 8000" -WindowStyle Normal
Start-Sleep -Seconds 1

# 前端
$frontendLog = Join-Path $PIDS_DIR "frontend.log"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$SCRIPT_DIR\client'; Write-Host '=== Frontend Dev Server ===' -ForegroundColor Magenta; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ 服务器启动成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  后端 API:  http://localhost:8000" -ForegroundColor White
Write-Host "  API 文档：http://localhost:8000/docs" -ForegroundColor White
Write-Host "  前端应用：http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "  停止服务器：运行 stop.ps1" -ForegroundColor Yellow
Write-Host ""
