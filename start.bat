@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Script Murder - Server Startup
echo ========================================
echo.

:: Check Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+.
    pause
    exit /b 1
)

:: Check Node.js
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js.
    pause
    exit /b 1
)

:: Check backend dependencies
echo [1/4] Checking backend dependencies...
pip show fastapi >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing backend dependencies...
    pip install -r requirements.txt
)

:: Check frontend dependencies
echo [2/4] Checking frontend dependencies...
if not exist "client\node_modules" (
    echo Installing frontend dependencies...
    cd client
    call npm install
    cd ..
)

:: Check .env file
echo [3/4] Checking configuration...
if not exist "server\.env" (
    if exist "server\.env.example" (
        echo Creating .env from template...
        copy server\.env.example server\.env
        echo Please edit server\.env to configure LLM server address
    ) else (
        echo [WARNING] No .env file found
    )
)

:: Start backend
echo [4/4] Starting backend server...
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
start "Script Murder Backend" cmd /k "uvicorn server.main:app --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul

:: Start frontend
echo Frontend: http://localhost:3000
start "Script Murder Frontend" cmd /k "cd client && npm run dev"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   Servers started successfully!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo API Docs:    http://localhost:8000/docs
echo Frontend:    http://localhost:3000
echo.
echo Stop servers: run stop.bat
echo.
pause
