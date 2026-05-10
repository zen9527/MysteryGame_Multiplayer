# Script Murder - 一键重启脚本
# 先停止再启动

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Script Murder - 重启服务器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "第一步：停止现有服务器..." -ForegroundColor Yellow
& "$PSScriptRoot\stop.ps1"

Write-Host ""
Write-Host "第二步：等待 2 秒..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "第三步：启动新服务器..." -ForegroundColor Yellow
& "$PSScriptRoot\start.ps1"
