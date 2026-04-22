@echo off
chcp 65001 >nul

echo ========================================
echo   Script Murder - Server Stop
echo ========================================
echo.

:: Stop backend (uvicorn)
echo Stopping backend server...
taskkill /FI "WINDOWTITLE eq Script Murder Backend*" /T /F >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Backend stopped
) else (
    echo [INFO] Backend was not running
)

:: Stop frontend (vite)
echo Stopping frontend server...
taskkill /FI "WINDOWTITLE eq Script Murder Frontend*" /T /F >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Frontend stopped
) else (
    echo [INFO] Frontend was not running
)

:: Clean up residual processes by port
echo.
echo Checking residual processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /F /PID %%a >nul 2>nul
    echo [Cleaned] Port 8000 process PID=%%a
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 2^>nul') do (
    taskkill /F /PID %%a >nul 2>nul
    echo [Cleaned] Port 3000 process PID=%%a
)

echo.
echo ========================================
echo   Servers stopped
echo ========================================
echo.
start "" cmd /c "timeout /t 2 ^&^& exit"
