@echo off
chcp 65001 >nul
title Script Murder - Stop

cd /d "%~dp0"
echo === Stopping Script Murder Servers ===
echo.

REM Kill backend (port 8000)
echo Stopping backend (port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] Killed PID %%a
    ) else (
        echo   [!] Process already stopped
    )
)

REM Kill frontend (port 3000)
echo Stopping frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] Killed PID %%a
    ) else (
        echo   [!] Process already stopped
    )
)

REM Kill any other frontend instances (port 3001, etc.)
echo Cleaning up old frontend instances...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":300[0-9].*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] Killed PID %%a
    )
)

REM Wait for ports to be released
echo.
echo Waiting for ports to be released...
timeout /t 2 /nobreak >nul

REM Verify ports are free
echo.
echo === Verification ===
set PORTS_FREE=1
for %%p in (8000, 3000) do (
    netstat -ano | findstr ":%%p.*LISTENING" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [!] Port %%p still in use
        set PORTS_FREE=0
    ) else (
        echo   [OK] Port %%p is free
    )
)

echo.
if !PORTS_FREE! equ 1 (
    echo === All servers stopped successfully ===
) else (
    echo === Some ports still in use, try running again ===
)
echo.
pause
