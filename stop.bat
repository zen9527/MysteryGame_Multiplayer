@echo off
chcp 65001 >nul
title Script Murder - Stop Servers
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0stop.ps1"
pause
