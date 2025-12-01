# GitHub Push Instructions for integrated-v2

## Issue
The terminal automation is having issues with log file locks. Please run the PowerShell script manually.

## Quick Steps

1. **Open PowerShell** in the project root: `Y:\AI\Cursor\Surveillance AI`

2. **Run the script**:
   ```powershell
   .\push-integrated-v2.ps1
   ```

## Or Run Commands Manually

If the script doesn't work, run these commands one by one:

```powershell
# 1. Create and switch to integrated-v2 branch
git checkout -b integrated-v2

# 2. Stage all changes
git add .

# 3. Verify no sensitive files (should return nothing)
git status --short | findstr /i "\.env \.db \.mp4 \.log provenance"

# 4. Commit (copy the full message from below)
git commit -m "feat: YouTube ingestion, media registry, and re-analysis capabilities" -m "Major Features:" -m "- Media Registry: JSON-backed cache for downloaded YouTube videos" -m "- POST /media/fetch: Probe formats and fetch/cache videos" -m "- Extended POST /analyze: Accept media_id for re-analysis without re-download" -m "- YouTube URL Ingestion: Dynamic format selection with yt-dlp" -m "- Run History: Preserve multiple analysis runs per video" -m "- Virtual Previews: Browser-based preview seeking without server files" -m "- Export on Demand: Generate MP4 clips with watermarking" -m "Backend Changes:" -m "- Added media_registry.py for media caching" -m "- Extended app.py with /media/fetch endpoint" -m "- Enhanced /analyze to support media_id parameter" -m "- Added preview_merge.py and time_utils.py utilities" -m "- Updated config with cache and YouTube settings" -m "- Updated .gitignore to exclude database files" -m "Frontend Changes:" -m "- Added UrlIngestForm component for YouTube URL input" -m "- Added VideoRangeSelector for analysis window selection" -m "- Added VirtualPreview component for browser-based previews" -m "- Enhanced Results page with run history dropdown" -m "- Updated Upload page with URL ingestion flow" -m "- Added cache verification and refetch UI" -m "- Cleaned up debug console.logs" -m "Documentation:" -m "- Updated README.md with new features and flow" -m "- Updated backend/README.md with new endpoints" -m "- Added architecture and QA documentation" -m "- Added migration and verification docs" -m "Breaking Changes: None (backward compatible)"

# 5. Push to remote
git push origin integrated-v2
```

## Alternative: Use Git GUI

If command line continues to have issues:

1. Open **Git GUI** or **GitHub Desktop**
2. Create a new branch: `integrated-v2`
3. Stage all changes
4. Review the files (ensure no `.env`, `.db`, `.mp4`, `.log` files)
5. Commit with the message above
6. Push to origin

## Verification

After pushing, verify at:
https://github.com/strangepace/Surveillance-AI/tree/integrated-v2

---

**Note**: The script `push-integrated-v2.ps1` includes all safety checks and will verify no sensitive files are being committed.

