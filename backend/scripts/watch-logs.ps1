# PowerShell script to watch cached re-analysis logs
# Usage: .\scripts\watch-logs.ps1

Write-Host "Starting log monitor for cached re-analysis..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

cd $PSScriptRoot\..
python scripts/watch_cached_analysis_logs.py

