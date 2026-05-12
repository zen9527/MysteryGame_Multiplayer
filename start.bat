@echo off
chcp 65001 >nul
title Script Murder - Start Servers

cd /d "%~dp0"

powershell -NoProfile -Command "$d = $PWD.Path; Write-Host '=== Starting Script Murder ===' -ForegroundColor Cyan; python --version 2>&1 | Out-Null; if ($LASTEXITCODE -ne 0) { Write-Host 'ERROR: Python not found' -ForegroundColor Red; pause; exit 1 }; node --version 2>&1 | Out-Null; if ($LASTEXITCODE -ne 0) { Write-Host 'ERROR: Node.js not found' -ForegroundColor Red; pause; exit 1 }; if (!(Test-Path 'client\node_modules')) { Write-Host 'Installing frontend...'; Push-Location client; npm install --silent; Pop-Location }; pip show fastapi --quiet 2>&1 | Out-Null; if ($LASTEXITCODE -ne 0) { Write-Host 'Installing backend...'; pip install -r requirements.txt --quiet }; if (!(Test-Path '.env') -and (Test-Path '.env.example')) { Copy-Item .env.example .env; Write-Host 'Created .env' }; Write-Host 'Starting backend (8000)...' -ForegroundColor Green; $beCmd = 'Set-Location ''' + $d + '''; uvicorn server.main:app --host 0.0.0.0 --port 8000'; Start-Process powershell -ArgumentList '-NoExit','-Command',$beCmd; Start-Sleep 1; Write-Host 'Starting frontend (3000)...' -ForegroundColor Green; $feCmd = 'Set-Location ''' + $d + '\client''; npm run dev'; Start-Process powershell -ArgumentList '-NoExit','-Command',$feCmd; Write-Host ''; Write-Host 'Servers started!' -ForegroundColor Yellow; Write-Host '  Backend:  http://localhost:8000' -ForegroundColor Yellow; Write-Host '  Frontend: http://localhost:3000' -ForegroundColor Yellow"

pause
