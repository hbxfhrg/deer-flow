@echo off
title Stop Practice Services

echo.
echo ============================================
echo   Stopping Practice Services
echo ============================================
echo.

REM Kill processes on port 8001 (backend)
echo Stopping backend (port 8001)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr "LISTENING"') do (
    echo   Killing PID %%a
    taskkill /f /pid %%a 2>nul
)

REM Kill processes on port 4000 (frontend)
echo Stopping frontend (port 4000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4000" ^| findstr "LISTENING"') do (
    echo   Killing PID %%a
    taskkill /f /pid %%a 2>nul
)

echo.
echo ============================================
echo   All services stopped
echo ============================================
echo.
pause
