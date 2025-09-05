@echo off
echo 🚀 Starting Surveillance AI Backend...
echo 🔧 Auto-configuring FFmpeg environment...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python and try again.
    pause
    exit /b 1
)

REM Start the backend with FFmpeg auto-configuration
python start_backend.py

echo.
echo 🛑 Backend stopped.
pause
