@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   剧本杀 - 服务器启动脚本
echo ========================================
echo.

:: 检查 Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 检查 Node.js
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

:: 检查后端依赖
echo [1/4] 检查后端依赖...
pip show fastapi >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 安装后端依赖...
    pip install -r requirements.txt
)

:: 检查前端依赖
echo [2/4] 检查前端依赖...
if not exist "client\node_modules" (
    echo 安装前端依赖...
    cd client
    npm install
    cd ..
)

:: 检查 .env 文件
echo [3/4] 检查配置文件...
if not exist "server\.env" (
    if exist "server\.env.example" (
        echo 未找到 .env 文件，从模板创建...
        copy server\.env.example server\.env
        echo 请编辑 server\.env 配置 LLM 服务器地址
    ) else (
        echo [警告] 未找到 .env 文件
    )
)

:: 启动后端
echo [4/4] 启动后端服务器...
echo 后端: http://localhost:8000
echo API 文档: http://localhost:8000/docs
start "剧本杀-后端" cmd /k "uvicorn server.main:app --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul

:: 启动前端
echo 前端: http://localhost:3000
start "剧本杀-前端" cmd /k "cd client ^&^& npm run dev"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   服务器启动完成！
echo ========================================
echo.
echo 后端 API: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo 前端页面: http://localhost:3000
echo.
echo 停止服务器: 运行 stop.bat
echo.
pause
