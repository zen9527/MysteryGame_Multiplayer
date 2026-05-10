@echo off
chcp 65001 >nul
REM Script Murder - Legacy stop script
REM 现在调用 PowerShell 版本（更可靠）

powershell -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
pause
