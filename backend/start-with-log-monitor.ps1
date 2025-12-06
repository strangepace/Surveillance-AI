# Start backend server with log monitoring
# This script starts the backend server and opens a second window for log monitoring

$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logMonitorScript = Join-Path $backendDir "scripts\watch_cached_analysis_logs.py"

Write-Host "Starting backend server with log monitoring..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal 1: Backend server (this window)" -ForegroundColor Yellow
Write-Host "Terminal 2: Log monitor (will open automatically)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C in this window to stop the server" -ForegroundColor Green
Write-Host "Press Ctrl+C in the log monitor window to stop monitoring" -ForegroundColor Green
Write-Host ""
Write-Host "Starting backend server..." -ForegroundColor Cyan
Write-Host ""

# Start log monitor in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendDir'; python '$logMonitorScript'"

# Start backend server in current window
cd $backendDir
python start_backend.py

