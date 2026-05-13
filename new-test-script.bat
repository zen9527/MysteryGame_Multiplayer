@echo off
chcp 65001 >nul
title Script Murder - New Test Script

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0new-test-script.ps1"

echo.
pause
