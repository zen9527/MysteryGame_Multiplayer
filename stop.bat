@echo off
chcp 65001 >nul

echo ========================================
echo   剧本杀 - 服务器停止脚本
echo ========================================
echo.

:: 停止 uvicorn (后端)
echo 停止后端服务器...
taskkill /FI "WINDOWTITLE eq 剧本杀 - 后端*" /T /F >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] 后端已停止
) else (
    echo [信息] 后端未运行
)

:: 停止 vite (前端)
echo 停止前端服务器...
taskkill /FI "WINDOWTITLE eq 剧本杀 - 前端*" /T /F >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] 前端已停止
) else (
    echo [信息] 前端未运行
)

:: 额外检查：如果有残留的 python/node 进程，也停止
echo.
echo 检查残留进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /F /PID %%a >nul 2>nul
    echo [清理] 端口 8000 进程 PID=%%a
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 2^>nul') do (
    taskkill /F /PID %%a >nul 2>nul
    echo [清理] 端口 3000 进程 PID=%%a
)

echo.
echo ========================================
echo   服务器已停止
echo ========================================
echo.
start "" cmd /c "timeout /t 2 ^&^& exit"
