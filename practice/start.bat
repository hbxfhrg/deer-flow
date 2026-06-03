@echo off
title DeerFlow 对练系统启动

echo.
echo ============================================
echo   DeerFlow Practice - One Click Start
echo ============================================
echo.

cd /d "%~dp0"

REM ===== Check python =====
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)
echo [OK] Python found

REM ===== Check node =====
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found in PATH
    pause
    exit /b 1
)
echo [OK] Node.js found

echo.

REM ===== Install backend deps if needed =====
echo [1/4] Checking backend dependencies...
cd backend
python -c "import fastapi, uvicorn, sqlalchemy, langchain_openai" >nul 2>&1
if %errorlevel% neq 0 (
    echo        Installing backend dependencies...
    pip install -r requirements.txt -q
)
echo        Backend deps OK
cd ..

REM ===== Install frontend deps if needed =====
echo [2/4] Checking frontend dependencies...
if not exist "node_modules" (
    echo        Installing frontend dependencies...
    call npm install
)
echo        Frontend deps OK

echo.
echo [3/4] Starting backend on port 8001...
start "Practice-Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

REM Wait for backend
echo        Waiting for backend to start...
ping -n 5 127.0.0.1 >nul

echo [4/4] Starting frontend on port 4000...
start "Practice-Frontend" cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo ============================================
echo   Startup Complete!
echo   Frontend : http://localhost:4000
echo   API Docs : http://localhost:8001/docs
echo   Health   : http://localhost:8001/health
echo ============================================
echo.
echo Press any key to close this window...
pause >nul
