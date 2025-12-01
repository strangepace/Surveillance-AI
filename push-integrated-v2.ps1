# PowerShell script to create and push integrated-v2 branch
# Run this from the project root: Y:\AI\Cursor\Surveillance AI

Write-Host "=== Creating integrated-v2 branch ===" -ForegroundColor Green

# Check current branch
$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch" -ForegroundColor Yellow

# Create and switch to integrated-v2
Write-Host "`nCreating integrated-v2 branch..." -ForegroundColor Yellow
git checkout -b integrated-v2
if ($LASTEXITCODE -ne 0) {
    Write-Host "Branch may already exist. Switching to it..." -ForegroundColor Yellow
    git checkout integrated-v2
}

# Stage all changes
Write-Host "`nStaging all changes..." -ForegroundColor Yellow
git add .

# Verify no sensitive files
Write-Host "`nChecking for sensitive files..." -ForegroundColor Yellow
$sensitive = git status --short | Select-String -Pattern "\.env|\.db|\.mp4|\.log|provenance"
if ($sensitive) {
    Write-Host "WARNING: Found potentially sensitive files:" -ForegroundColor Red
    $sensitive | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    Write-Host "`nPlease review before committing!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✓ No sensitive files found" -ForegroundColor Green
}

# Show what will be committed
Write-Host "`nFiles to be committed:" -ForegroundColor Yellow
git status --short

# Commit
Write-Host "`nCommitting changes..." -ForegroundColor Yellow
$commitMsg = @"
feat: YouTube ingestion, media registry, and re-analysis capabilities

Major Features:
- Media Registry: JSON-backed cache for downloaded YouTube videos
- POST /media/fetch: Probe formats and fetch/cache videos
- Extended POST /analyze: Accept media_id for re-analysis without re-download
- YouTube URL Ingestion: Dynamic format selection with yt-dlp
- Run History: Preserve multiple analysis runs per video
- Virtual Previews: Browser-based preview seeking without server files
- Export on Demand: Generate MP4 clips with watermarking

Backend Changes:
- Added media_registry.py for media caching
- Extended app.py with /media/fetch endpoint
- Enhanced /analyze to support media_id parameter
- Added preview_merge.py and time_utils.py utilities
- Updated config with cache and YouTube settings
- Updated .gitignore to exclude database files

Frontend Changes:
- Added UrlIngestForm component for YouTube URL input
- Added VideoRangeSelector for analysis window selection
- Added VirtualPreview component for browser-based previews
- Enhanced Results page with run history dropdown
- Updated Upload page with URL ingestion flow
- Added cache verification and refetch UI
- Cleaned up debug console.logs

Documentation:
- Updated README.md with new features and flow
- Updated backend/README.md with new endpoints
- Added architecture and QA documentation
- Added migration and verification docs

Breaking Changes: None (backward compatible)
"@

git commit -m $commitMsg

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Commit successful!" -ForegroundColor Green
    
    # Push to remote
    Write-Host "`nPushing to remote..." -ForegroundColor Yellow
    git push origin integrated-v2
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓✓✓ Successfully pushed integrated-v2 to GitHub! ✓✓✓" -ForegroundColor Green
        Write-Host "`nYou can view it at: https://github.com/strangepace/Surveillance-AI/tree/integrated-v2" -ForegroundColor Cyan
    } else {
        Write-Host "`n✗ Push failed. Please check your git credentials and try again." -ForegroundColor Red
    }
} else {
    Write-Host "`n✗ Commit failed. Please check the error above." -ForegroundColor Red
}

