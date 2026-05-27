@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置颜色
color 0A

:: 配置参数
set "BACKEND_PORT=8001"
set "FRONTEND_PORT=5173"
set "PYTHON_VERSION=3.12"
set "NODE_VERSION=18"

echo ================================================
echo          DeerFlow AI对练系统一键部署脚本
echo ================================================
echo 后端端口: %BACKEND_PORT%
echo 前端端口: %FRONTEND_PORT%
echo ================================================
echo.

:: 1. 检查 Python 版本
echo [1/6] 检查 Python 环境...
python --version 2>&1 | findstr "Python 3." >nul
if %errorlevel% neq 0 (
    echo 错误：未找到 Python，请安装 Python %PYTHON_VERSION%+
    pause
    exit /b 1
)

:: 2. 检查 Node.js 版本
echo.
echo [2/6] 检查 Node.js 环境...
node --version 2>&1 | findstr "v18\|v19\|v20\|v21\|v22" >nul
if %errorlevel% neq 0 (
    echo 错误：未找到 Node.js，请安装 Node.js %NODE_VERSION%+
    pause
    exit /b 1
)

:: 3. 检查 MySQL 连接（可选）
echo.
echo [3/6] 检查数据库配置...
if not exist "backend/app/gateway/.env" (
    echo 警告：未找到 .env 文件，请确保数据库配置正确
    echo 请在 backend/app/gateway/.env 中配置数据库连接
)

:: 4. 安装后端依赖
echo.
echo [4/6] 安装后端依赖...
cd backend
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate.bat >nul

echo 升级 pip...
python -m pip install --upgrade pip >nul

echo 安装项目依赖...
pip install -e . -e packages/harness asyncmy >nul
if %errorlevel% neq 0 (
    echo 错误：后端依赖安装失败
    pause
    exit /b 1
)
deactivate

:: 5. 构建前端
echo.
echo [5/6] 构建前端...
cd ..\practice

if not exist "node_modules" (
    echo 安装前端依赖...
    npm install --legacy-peer-deps >nul
    if %errorlevel% neq 0 (
        echo 错误：前端依赖安装失败
        pause
        exit /b 1
    )
)

echo 构建生产版本...
npm run build >nul
if %errorlevel% neq 0 (
    echo 错误：前端构建失败
    pause
    exit /b 1
)

:: 6. 启动服务
echo.
echo [6/6] 启动服务...

:: 终止可能存在的服务
echo 清理端口占用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001"') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 启动后端服务
cd ..\backend
call venv\Scripts\activate.bat >nul
echo 启动后端服务...
start "DeerFlow Backend" python -m uvicorn app.gateway.main:app --host 0.0.0.0 --port %BACKEND_PORT%

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端开发服务器
cd ..\practice
echo 启动前端开发服务器...
start "DeerFlow Frontend" npm run dev -- --host 0.0.0.0 --port %FRONTEND_PORT%

:: 完成提示
echo.
echo ================================================
echo              部署完成！
echo ================================================
echo.
echo 服务状态:
echo   - 后端服务: http://localhost:%BACKEND_PORT%
echo   - 前端页面: http://localhost:%FRONTEND_PORT%
echo.
echo 数据库配置文件: backend/app/gateway/.env
echo 前端构建产物: practice/dist/
echo.
echo 按任意键打开前端页面...
pause >nul
start http://localhost:%FRONTEND_PORT%