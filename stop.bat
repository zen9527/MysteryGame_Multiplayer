@echo off
chcp 65001 >nul
title Script Murder - Stop

powershell -Command ^
"$ports = @(8000, 3000); ^
foreach ($port in $ports) { ^
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1; ^
    if ($conn) { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host \"Port $port stopped\" -ForegroundColor Green } ^
    else { Write-Host \"Port $port not in use\" -ForegroundColor Gray } ^
}"

echo.
pause
