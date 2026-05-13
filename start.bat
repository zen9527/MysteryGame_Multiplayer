@echo off
chcp 65001 >nul
title Script Murder - Start Servers

cd /d "%~dp0"

echo === 启动 Script Murder ===
echo.

powershell -NoProfile -Command ^
"$scriptDir = $PWD.Path; ^
Write-Host '检查环境...' -ForegroundColor Cyan; ^
^
# Check Python ^
try { ^
    $pythonVersion = python --version 2>&1; ^
    Write-Host \"  ✓ Python: $pythonVersion\" -ForegroundColor Green; ^
} catch { ^
    Write-Host '  ✗ Python 未安装' -ForegroundColor Red; ^
    pause; ^
    exit 1; ^
} ^
^
# Check Node.js ^
try { ^
    $nodeVersion = node --version 2>&1; ^
    Write-Host \"  ✓ Node.js: $nodeVersion\" -ForegroundColor Green; ^
} catch { ^
    Write-Host '  ✗ Node.js 未安装' -ForegroundColor Red; ^
    pause; ^
    exit 1; ^
} ^
^
# Install frontend dependencies if needed ^
if (!(Test-Path 'client\node_modules')) { ^
    Write-Host '  安装前端依赖...' -ForegroundColor Yellow; ^
    Push-Location client; ^
    npm install --silent; ^
    Pop-Location; ^
    Write-Host '  ✓ 前端依赖已安装' -ForegroundColor Green; ^
} ^
^
# Install backend dependencies if needed ^
try { ^
    pip show fastapi --quiet 2>&1; ^
} catch { ^
    Write-Host '  安装后端依赖...' -ForegroundColor Yellow; ^
    pip install -r requirements.txt --quiet; ^
    Write-Host '  ✓ 后端依赖已安装' -ForegroundColor Green; ^
} ^
^
# Create .env if missing ^
if (!(Test-Path '.env') -and (Test-Path '.env.example')) { ^
    Copy-Item .env.example .env; ^
    Write-Host '  ✓ 创建了 .env 文件' -ForegroundColor Green; ^
} ^
^
Write-Host ''; ^
Write-Host '启动后端 (端口 8000)...' -ForegroundColor Green; ^
$backendCommand = \"Set-Location '$scriptDir'; uvicorn server.main:app --host 0.0.0.0 --port 8000\"; ^
Start-Process powershell -ArgumentList '-NoExit', '-Command', $backendCommand -WindowStyle Normal; ^
Start-Sleep 2; ^
^
Write-Host '启动前端 (端口 3000)...' -ForegroundColor Green; ^
$frontendCommand = \"Set-Location '$scriptDir\client'; npm run dev\"; ^
Start-Process powershell -ArgumentList '-NoExit', '-Command', $frontendCommand -WindowStyle Normal; ^
^
Write-Host ''; ^
Write-Host '=== 服务器已启动 ===' -ForegroundColor Yellow; ^
Write-Host '  后端：http://localhost:8000' -ForegroundColor Yellow; ^
Write-Host '  前端：http://localhost:3000' -ForegroundColor Yellow; ^
Write-Host ''; ^
Write-Host '提示：关闭窗口即可停止服务器，或使用 stop.bat' -ForegroundColor Gray"

echo.
pause
