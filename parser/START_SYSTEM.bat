@echo off
echo ========================================
echo   DOCUMENT PROCESSING SYSTEM
echo ========================================
echo.
echo Starting all components...
echo.

REM Start Redis Server
echo [1/4] Starting Redis Server...
start "Redis Server" cmd /k "cd /d C:\Program Files\Redis && redis-server.exe"
timeout /t 3 /nobreak >nul

REM Start Worker 1
echo [2/4] Starting Worker 1...
start "Worker 1" cmd /k "cd /d %~dp0 && python worker.py"
timeout /t 2 /nobreak >nul

REM Start Worker 2
echo [3/4] Starting Worker 2...
start "Worker 2" cmd /k "cd /d %~dp0 && python worker.py"
timeout /t 2 /nobreak >nul

REM Start Monitor
echo [4/4] Starting Monitor...
start "Monitor" cmd /k "cd /d %~dp0 && python monitor.py"

echo.
echo ========================================
echo   ALL COMPONENTS STARTED!
echo ========================================
echo.
echo Components running:
echo   - Redis Server
echo   - Worker 1
echo   - Worker 2
echo   - S3 Monitor
echo.
echo To view dashboard, run: python dashboard.py
echo To stop all, close all windows or press Ctrl+C
echo.
pause
