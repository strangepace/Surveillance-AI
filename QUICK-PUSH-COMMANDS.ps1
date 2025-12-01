# Quick Push Commands - Copy and paste into PowerShell
# Run from: Y:\AI\Cursor\Surveillance AI

Write-Host "=== Step 1: Stop Background Processes ===" -ForegroundColor Cyan
Get-Process powershell | Where-Object { $_.Id -ne $PID } | Stop-Process -Force
Write-Host "Done. Waiting 2 seconds..." -ForegroundColor Green
Start-Sleep -Seconds 2

Write-Host "`n=== Step 2: Navigate to Project ===" -ForegroundColor Cyan
cd "Y:\AI\Cursor\Surveillance AI"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Green

Write-Host "`n=== Step 3: Check Current Branch ===" -ForegroundColor Cyan
$branch = git branch --show-current
Write-Host "Current branch: $branch" -ForegroundColor Yellow

Write-Host "`n=== Step 4: Create integrated-v2 Branch ===" -ForegroundColor Cyan
git checkout -b integrated-v2 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Branch may exist, switching..." -ForegroundColor Yellow
    git checkout integrated-v2
}

Write-Host "`n=== Step 5: Stage All Changes ===" -ForegroundColor Cyan
git add .
Write-Host "Files staged." -ForegroundColor Green

Write-Host "`n=== Step 6: Safety Check (No sensitive files) ===" -ForegroundColor Cyan
$sensitive = git diff --cached --name-only | findstr /i "\.env \.db \.mp4 \.log provenance"
if ($sensitive) {
    Write-Host "WARNING: Sensitive files found!" -ForegroundColor Red
    $sensitive
    Write-Host "`nSTOPPING. Please review files above." -ForegroundColor Red
    exit 1
} else {
    Write-Host "✓ No sensitive files found. Safe to proceed." -ForegroundColor Green
}

Write-Host "`n=== Step 7: Show What Will Be Committed ===" -ForegroundColor Cyan
$fileCount = (git diff --cached --name-only | Measure-Object -Line).Lines
Write-Host "Files to commit: $fileCount" -ForegroundColor Yellow
git diff --cached --name-only | Select-Object -First 10
if ($fileCount -gt 10) {
    Write-Host "... and $($fileCount - 10) more files" -ForegroundColor Gray
}

Write-Host "`n=== Step 8: Commit ===" -ForegroundColor Cyan
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "feat: YouTube ingestion, media registry, and re-analysis capabilities" -m "Major Features: Media Registry, POST /media/fetch, Extended /analyze with media_id, YouTube URL Ingestion, Run History, Virtual Previews, Export on Demand" -m "Backend: Added media_registry.py, extended app.py, added utilities, updated config and .gitignore" -m "Frontend: Added UrlIngestForm, VideoRangeSelector, VirtualPreview, enhanced Results page, updated Upload page" -m "Documentation: Updated READMEs, added architecture and QA docs" -m "Breaking Changes: None (backward compatible)"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Commit successful!" -ForegroundColor Green
    
    Write-Host "`n=== Step 9: Push to GitHub ===" -ForegroundColor Cyan
    Write-Host "Pushing to origin/integrated-v2..." -ForegroundColor Yellow
    git push origin integrated-v2
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓✓✓ SUCCESS! Branch pushed to GitHub! ✓✓✓" -ForegroundColor Green
        Write-Host "`nView at: https://github.com/strangepace/Surveillance-AI/tree/integrated-v2" -ForegroundColor Cyan
    } else {
        Write-Host "`n✗ Push failed. Check error above." -ForegroundColor Red
        Write-Host "You may need to authenticate or check your git credentials." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n✗ Commit failed. Check error above." -ForegroundColor Red
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan

