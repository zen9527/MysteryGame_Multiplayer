@echo off
chcp 65001 >nul
title Script Murder - Stop Servers

echo === 停止 Script Murder ===
echo.

powershell -NoProfile -Command ^
"$ports = @(8000, 3000); ^
foreach ($port in $ports) { ^
    try { ^
        $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction Stop | Select-Object -First 1; ^
        if ($conn) { ^
            $processId = $conn.OwningProcess; ^
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue; ^
            if ($process) { ^
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue; ^
                Write-Host \"已停止端口 $port (进程：$processId - $($process.ProcessName))\" -ForegroundColor Green; ^
            } else { ^
                Write-Host \"端口 $port 有连接但进程不存在\" -ForegroundColor Yellow; ^
            } ^
        } else { ^
            Write-Host \"端口 $port 未被使用\" -ForegroundColor Gray; ^
        } ^
    } catch { ^
        Write-Host \"检查端口 $port 时出错：$_\" -ForegroundColor Red; ^
    } ^
}; ^
Write-Host ''; ^
Write-Host '服务器已停止。' -ForegroundColor Yellow"

echo.
pause
