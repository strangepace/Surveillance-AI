# Stop any background log-watching processes
# This should free up the log file locks

Write-Host "Stopping log-watching processes..." -ForegroundColor Yellow

# Find and stop PowerShell processes that might be tailing logs
$processes = Get-Process | Where-Object {
    $_.ProcessName -eq "powershell" -or $_.ProcessName -eq "pwsh"
} | Where-Object {
    $_.CommandLine -like "*Get-Content*" -or 
    $_.CommandLine -like "*logs*" -or
    $_.CommandLine -like "*Wait*"
}

if ($processes) {
    Write-Host "Found $($processes.Count) potentially blocking processes" -ForegroundColor Yellow
    $processes | ForEach-Object {
        Write-Host "  Stopping PID: $($_.Id) - $($_.ProcessName)" -ForegroundColor Cyan
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "`nProcesses stopped. Try git commands again." -ForegroundColor Green
} else {
    Write-Host "No blocking processes found." -ForegroundColor Green
}

# Alternative: Just kill all PowerShell processes (use with caution!)
# Get-Process powershell | Where-Object { $_.Id -ne $PID } | Stop-Process -Force

