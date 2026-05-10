# Script Murder - Stop Servers
Write-Host "=== Stopping Script Murder ===" -ForegroundColor Cyan

# Stop by port
$ports = @(8000, 3000)
foreach ($port in $ports) {
    $procs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($procs) {
        foreach ($id in $procs) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
        Write-Host "Stopped port $port" -ForegroundColor Green
    } else {
        Write-Host "Port $port not in use" -ForegroundColor Gray
    }
}

Write-Host "`nServers stopped." -ForegroundColor Yellow
