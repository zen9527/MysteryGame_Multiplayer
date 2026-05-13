@echo off
chcp 65001 >nul
title Script Murder - Stop Servers

echo === 停止 Script Murder ===
echo.

REM Stop port 8000 (backend)
powershell -Command "$p = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1; if ($p) { Stop-Process -Id $p.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host '已停止端口 8000' -ForegroundColor Green } else { Write-Host '端口 8000 未被使用' -ForegroundColor Gray }"

REM Stop port 3000 (frontend)
powershell -Command "$p = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -First 1; if ($p) { Stop-Process -Id $p.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host '已停止端口 3000' -ForegroundColor Green } else { Write-Host '端口 3000 未被使用' -ForegroundColor Gray }"

echo.
echo 服务器已停止。
echo.
pause
