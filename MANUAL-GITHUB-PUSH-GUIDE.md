# Manual GitHub Push Guide - Step by Step

## Terminal: Use PowerShell (Recommended)

**Why PowerShell?**
- Better error handling
- More readable output
- Native support for git commands
- Better process management

**How to Open:**
- Press `Win + X` → Select "Windows PowerShell" or "Terminal"
- Or search "PowerShell" in Start Menu
- Navigate to project: `cd "Y:\AI\Cursor\Surveillance AI"`

---

## Step-by-Step Commands

### Step 1: Stop Background Processes (Fix Log File Lock)

**Open PowerShell** and run:

```powershell
# Check current directory
cd "Y:\AI\Cursor\Surveillance AI"

# List running PowerShell processes (to see what's running)
Get-Process powershell | Format-Table Id, ProcessName, StartTime -AutoSize

# Stop all other PowerShell processes (except current one)
Get-Process powershell | Where-Object { $_.Id -ne $PID } | Stop-Process -Force

# Verify they're stopped
Get-Process powershell
# Should only show 1 process (your current session)
```

**Expected Output:**
- First command shows all PowerShell processes
- Second command stops them (no output if successful)
- Third command should show only 1 process

---

### Step 2: Verify Current Branch and Status

```powershell
# Make sure you're in the project root
cd "Y:\AI\Cursor\Surveillance AI"

# Check current branch
git branch --show-current
# Expected: "integrated-dev"

# Check git status (should show modified/new files)
git status
```

**Expected Output:**
- Current branch: `integrated-dev`
- Status shows modified files (README.md, backend/app.py, etc.)
- Untracked files (media_registry.py, UrlIngestForm.tsx, etc.)

---

### Step 3: Verify No Sensitive Files Will Be Committed

```powershell
# Check for sensitive files in git status
git status --short | findstr /i "\.env \.db \.mp4 \.log provenance"

# Should return NOTHING (empty output = good!)
# If you see any files, STOP and review them
```

**Expected Output:**
- **Empty output** (this is good - means no sensitive files)
- If you see files, DO NOT proceed - review them first

---

### Step 4: Create integrated-v2 Branch

```powershell
# Create and switch to new branch
git checkout -b integrated-v2
```

**Expected Output:**
```
Switched to a new branch 'integrated-v2'
```

**If you see "branch already exists":**
```powershell
# Switch to existing branch
git checkout integrated-v2
```

---

### Step 5: Stage All Changes

```powershell
# Stage all modified and new files
git add .

# Verify what's staged
git status --short
```

**Expected Output:**
- Shows all files with `M` (modified) or `??` (new) now have `M` or `A` (added)
- Should see:
  - `.gitignore` (M)
  - `README.md` (M)
  - `backend/app.py` (M)
  - `backend/media_registry.py` (A - new)
  - `frontend/src/components/UrlIngestForm.tsx` (A - new)
  - etc.

---

### Step 6: Final Safety Check

```powershell
# Double-check no sensitive files are staged
git diff --cached --name-only | findstr /i "\.env \.db \.mp4 \.log provenance"

# Should return NOTHING
# Also check the count of files
git diff --cached --name-only | Measure-Object -Line
```

**Expected Output:**
- First command: **Empty** (no sensitive files)
- Second command: Shows line count (should be ~27-30 files)

---

### Step 7: Commit Changes

**Option A: Single Line Commit (Easier)**

```powershell
git commit -m "feat: YouTube ingestion, media registry, and re-analysis capabilities" -m "Major Features: Media Registry, POST /media/fetch, Extended /analyze with media_id, YouTube URL Ingestion, Run History, Virtual Previews, Export on Demand" -m "Backend: Added media_registry.py, extended app.py, added utilities, updated config and .gitignore" -m "Frontend: Added UrlIngestForm, VideoRangeSelector, VirtualPreview, enhanced Results page, updated Upload page" -m "Documentation: Updated READMEs, added architecture and QA docs" -m "Breaking Changes: None (backward compatible)"
```

**Option B: Multi-line Commit (More Detailed)**

Create a commit message file first:

```powershell
# Create commit message file
@"
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
"@ | Out-File -FilePath commit-message.txt -Encoding utf8

# Commit using the file
git commit -F commit-message.txt

# Clean up
Remove-Item commit-message.txt
```

**Expected Output:**
```
[integrated-v2 abc1234] feat: YouTube ingestion, media registry, and re-analysis capabilities
 27 files changed, 2914 insertions(+), 107 deletions(-)
```

---

### Step 8: Push to GitHub

```powershell
# Push to remote repository
git push origin integrated-v2
```

**Expected Output (First Time):**
```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX), done.
Delta compression using up to X threads
Compressing objects: 100% (XX/XX), done.
Writing objects: 100% (XX/XX), XXX KB | XXX.XX MiB/s, done.
Total XX (delta XX), reused XX (delta XX), pack-reused XX
remote: Resolving deltas: 100% (XX/XX), completed with XX local objects.
To https://github.com/strangepace/Surveillance-AI.git
 * [new branch]      integrated-v2 -> integrated-v2
```

**If you see authentication error:**
- You may need to authenticate with GitHub
- Use GitHub Personal Access Token or SSH key
- Or use GitHub Desktop/Git Credential Manager

---

### Step 9: Verify on GitHub

1. Open browser: https://github.com/strangepace/Surveillance-AI
2. Click on branch dropdown (should show "integrated-v2")
3. Select "integrated-v2" branch
4. Verify files are there

**Or check via command:**
```powershell
# Verify remote branch exists
git ls-remote --heads origin integrated-v2
```

**Expected Output:**
```
abc1234...refs/heads/integrated-v2
```

---

## Troubleshooting

### Issue: "Log file is already in use"
**Solution:** Run Step 1 again to stop background processes

### Issue: "Branch already exists"
**Solution:** 
```powershell
git checkout integrated-v2
# Then continue from Step 5
```

### Issue: "Authentication failed"
**Solution:**
```powershell
# Check remote URL
git remote -v

# If using HTTPS, you may need to set credentials
git config --global credential.helper manager-core

# Or use SSH instead
git remote set-url origin git@github.com:strangepace/Surveillance-AI.git
```

### Issue: "Nothing to commit"
**Solution:**
```powershell
# Check if files are already committed
git log --oneline -1

# If yes, just push:
git push origin integrated-v2
```

### Issue: "Files are not staged"
**Solution:**
```powershell
# Check what's not staged
git status

# Stage specific files or all:
git add .
```

---

## Quick Reference (Copy-Paste Commands)

```powershell
# 1. Navigate to project
cd "Y:\AI\Cursor\Surveillance AI"

# 2. Stop background processes
Get-Process powershell | Where-Object { $_.Id -ne $PID } | Stop-Process -Force

# 3. Create branch
git checkout -b integrated-v2

# 4. Stage all
git add .

# 5. Safety check
git diff --cached --name-only | findstr /i "\.env \.db \.mp4 \.log provenance"

# 6. Commit
git commit -m "feat: YouTube ingestion, media registry, and re-analysis capabilities" -m "See INTEGRATED-V2-MIGRATION-PLAN.md for full details"

# 7. Push
git push origin integrated-v2
```

---

## What Files Will Be Committed?

**Modified (14 files):**
- `.gitignore`
- `README.md`
- `backend/README.md`
- `backend/analyzer.py`
- `backend/app.py`
- `backend/config/clip_config.yaml`
- `backend/requirements.txt`
- `backend/utils/ffmpeg.py`
- `frontend/src/components/PromptChipsInput.tsx`
- `frontend/src/components/ui/slider.tsx`
- `frontend/src/context/UploadContext.tsx`
- `frontend/src/pages/Configure.tsx`
- `frontend/src/pages/Results.tsx`
- `frontend/src/pages/Upload.tsx`

**New (13+ files):**
- `backend/media_registry.py`
- `backend/utils/preview_merge.py`
- `backend/utils/time_utils.py`
- `frontend/src/components/UrlIngestForm.tsx`
- `frontend/src/components/VideoRangeSelector.tsx`
- `frontend/src/components/VirtualPreview.tsx`
- Documentation files
- Migration plan files

**Deleted (2 files):**
- `frontend/src/components/VideoRangeSelectorOld.tsx`
- `frontend/src/components/VideoRangeSelectorSimple.tsx`

---

**Total:** ~27-30 files, ~2900+ lines added

---

## Success Indicators

✅ Branch created: `git branch` shows `* integrated-v2`  
✅ Files staged: `git status` shows files with `M` or `A`  
✅ Commit successful: Shows commit hash  
✅ Push successful: Shows "new branch" message  
✅ GitHub visible: Branch appears on GitHub website  

---

**Ready? Start with Step 1!**

