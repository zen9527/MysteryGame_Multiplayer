@echo off
chcp 65001 >nul
title Script Murder - Start Servers

cd /d "%~dp0"

echo === 启动 Script Murder ===
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 未安装
    pause
    exit /b 1
)
echo [OK] Python 已安装

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js 未安装
    pause
    exit /b 1
)
echo [OK] Node.js 已安装

REM Install frontend dependencies if needed
if not exist "client\node_modules" (
    echo [INFO] 安装前端依赖...
    cd client
    call npm install
    cd ..
    echo [OK] 前端依赖已安装
)

REM Install backend dependencies if needed
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] 安装后端依赖...
    pip install -r requirements.txt
    echo [OK] 后端依赖已安装
)

REM Create .env if missing
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] 创建了 .env 文件
    )
)

echo.
echo [INFO] 启动后端 (端口 8000)...
start "Script Murder - Backend" powershell -NoExit -Command "cd '%~dp0'; uvicorn server.main:app --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo [INFO] 启动前端 (端口 3000)...
start "Script Murder - Frontend" powershell -NoExit -Command "cd '%~dp0client'; npm run dev"

echo.
echo === 服务器已启动 ===
echo   后端：http://localhost:8000
echo   前端：http://localhost:3000
echo.
echo 提示：关闭窗口即可停止服务器，或使用 stop.bat
echo.
pause
