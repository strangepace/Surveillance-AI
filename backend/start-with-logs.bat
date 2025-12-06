@echo off
REM Start backend server with log monitoring
echo Starting backend server with log monitoring...
echo.
echo Terminal 1: Backend server (this window)
echo Terminal 2: Log monitor (will open automatically)
echo.
echo Press Ctrl+C in this window to stop the server
echo Press Ctrl+C in the log monitor window to stop monitoring
echo.

REM Start log monitor in a new window
start "Log Monitor" cmd /k "cd /d %~dp0 && python scripts\watch_cached_analysis_logs.py"

REM Start backend server in current window
cd /d %~dp0
python start_backend.py

pause

