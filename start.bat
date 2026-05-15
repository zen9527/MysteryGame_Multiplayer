@echo off
chcp 65001 >nul
title Script Murder - Start

cd /d "%~dp0"
echo === Starting Script Murder ===
echo.

REM Check Python
python --version >nul 2>&1 || (echo ERROR: Python not found & pause & exit /b 1)
echo [OK] Python

REM Check Node.js
node --version >nul 2>&1 || (echo ERROR: Node.js not found & pause & exit /b 1)
echo [OK] Node.js

REM Install dependencies
if not exist "client\node_modules" (echo Installing frontend... & cd client & npm install & cd ..)
pip show fastapi >nul 2>&1 || (echo Installing backend... & pip install -r requirements.txt)

REM Create .env
if not exist ".env" if exist ".env.example" copy .env.example .env >nul

REM Check if ports are already in use
echo.
echo Checking ports...
set PORTS_OCCUPIED=0
for %%p in (8000, 3000) do (
    netstat -ano | findstr ":%%p.*LISTENING" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [!] Port %%p is already in use
        set PORTS_OCCUPIED=1
    )
)

if !PORTS_OCCUPIED! equ 1 (
    echo.
    echo Please run stop.bat first to free the ports, or manually kill the processes.
    pause
    exit /b 1
)

REM Start servers
echo Starting backend (8000)...
start "Backend" cmd /c "cd /d "%~dp0" && uvicorn server.main:app --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul

echo Starting frontend (3000)...
start "Frontend" cmd /c "cd /d "%~dp0client" && npm run dev"

echo.
echo === Servers Started ===
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo To stop servers, run: stop.bat
pause
