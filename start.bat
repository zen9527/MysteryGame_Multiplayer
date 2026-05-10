@echo off
chcp 65001 >nul
title Script Murder - Start Servers
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0start.ps1"
pause
