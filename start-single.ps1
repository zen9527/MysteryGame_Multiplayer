# Script Murder - 单窗口模式（前后端日志合并显示）
# 适合开发调试，一个窗口同时看两个服务的日志

$ErrorActionPreference = "Continue"
$SCRIPT_DIR = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script Murder - 单窗口模式" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示：按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
Write-Host ""

# 切换到脚本目录
Set-Location $SCRIPT_DIR

# 检查环境
Write-Host "[检查] Python 和 Node.js..." -ForegroundColor Yellow
try { python --version 2>&1 | Out-Null; Write-Host "  ✓ Python OK" -ForegroundColor Green } catch { Write-Host "  ✗ Python 缺失"; exit 1 }
try { node --version 2>&1 | Out-Null; Write-Host "  ✓ Node.js OK" -ForegroundColor Green } catch { Write-Host "  ✗ Node.js 缺失"; exit 1 }

# 检查依赖
if (!(Test-Path "client\node_modules")) {
    Write-Host "[安装] 前端依赖..." -ForegroundColor Yellow
    Set-Location client; npm install --silent; Set-Location ..
}
try { pip show fastapi --quiet 2>&1 | Out-Null } catch {
    Write-Host "[安装] 后端依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt --quiet
}

# 检查配置
if (!(Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item .env.example .env
    Write-Host "[提示] 请检查 .env 中的 LLM_ENDPOINT 配置" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动服务（按 Ctrl+C 停止）" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 创建 PowerShell job 来运行后端
$backendJob = Start-Job -ScriptBlock {
    Write-Host "=== Backend (8000) ===" -ForegroundColor Cyan
    Set-Location $using:SCRIPT_DIR
    uvicorn server.main:app --host 0.0.0.0 --port 8000
}

Start-Sleep -Seconds 2

# 运行前端（当前线程）
Write-Host "=== Frontend (3000) ===" -ForegroundColor Magenta
Set-Location client
npm run dev

# 清理后端 job
Stop-Job $backendJob
Remove-Job $backendJob
