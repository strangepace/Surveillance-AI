# Integrated-v2 Migration Plan

## Overview
This document outlines the differences between `integrated-v1` (last GitHub commit) and the current local work, and provides a safe migration plan to create `integrated-v2` branch.

---

## 🔍 Differences Analysis

### Modified Files (14 files)
1. **README.md** (root) - Updated with YouTube ingestion, media registry, re-analysis features
2. **backend/README.md** - Added `/media/fetch` endpoint docs, media_id analysis flow
3. **backend/analyzer.py** - Enhanced for media_id support, re-analysis
4. **backend/app.py** - Major additions:
   - `POST /media/fetch` endpoint (probe + fetch actions)
   - Media registry integration
   - Extended `POST /analyze` to accept `media_id`
   - YouTube format inspection with `yt-dlp`
   - Browser-safe MP4 re-encoding
5. **backend/config/clip_config.yaml** - Added:
   - `cache.max_total_gb: 8`
   - `youtube.allow: true`
   - Preview merge settings
   - Export settings
   - Media serving settings
6. **backend/requirements.txt** - Added `yt-dlp` dependency
7. **backend/utils/ffmpeg.py** - Enhanced FFmpeg utilities
8. **frontend/src/components/PromptChipsInput.tsx** - Added `disabled` prop
9. **frontend/src/components/ui/slider.tsx** - UI component updates
10. **frontend/src/context/UploadContext.tsx** - Added `prompts` to context
11. **frontend/src/pages/Configure.tsx** - Re-analysis UI updates
12. **frontend/src/pages/Results.tsx** - Major additions:
    - Run history dropdown (preserve multiple analysis runs)
    - Re-analysis with same media_id
    - Cache verification and refetch UI
    - Source meta display (YouTube • format • duration)
13. **frontend/src/pages/Upload.tsx** - Integrated URL ingestion flow

### New Files (13 files)
1. **backend/media_registry.py** - JSON-backed media cache registry
2. **backend/provenance.db** - SQLite database for provenance tracking (should be gitignored)
3. **backend/test_url_ingestion_examples.md** - Test documentation
4. **backend/utils/preview_merge.py** - Preview merging utilities
5. **backend/utils/time_utils.py** - Time validation utilities
6. **docs/qa/url_ingestion_smoke_test.md** - QA documentation
7. **docs/status/hybrid_preview_architecture_status.md** - Architecture docs
8. **frontend/src/components/UrlIngestForm.tsx** - YouTube URL ingestion UI
9. **frontend/src/components/VideoRangeSelector.tsx** - Analysis window selector
10. **frontend/src/components/VideoRangeSelectorOld.tsx** - Legacy component (can remove?)
11. **frontend/src/components/VideoRangeSelectorSimple.tsx** - Alternative selector
12. **frontend/src/components/VirtualPreview.tsx** - Virtual preview component
13. **resume_docs/** - Resume documentation folder (should be committed)

---

## 🚨 Critical Safety Checks

### .gitignore Review
Current `.gitignore` properly excludes:
- ✅ `.env` and `.env.*` (except `.env.example`)
- ✅ `node_modules/`
- ✅ `__pycache__/`
- ✅ `*.log` and `logs/`
- ✅ `content/` (uploads, frames, previews)
- ✅ `results/` (previews, JSON, downloads)
- ✅ `*.mp4`, `*.avi`, etc. (video files)
- ✅ `backend/ffmpeg/` (large binaries)
- ✅ `*.db` (database files)

**⚠️ Potential Issues:**
- `backend/provenance.db` is currently untracked (good - should stay ignored)
- Need to verify no `.env` files are accidentally tracked
- Need to check if `media_registry.json` should be gitignored (it's in `content/uploads/` which is already ignored)

### .env Files Status
- ✅ No `.env` files found in search (good)
- ⚠️ No `.env.example` files found - should we create one?
- Recommendation: Create `.env.example` files for both frontend and backend

---

## 📋 Pre-Migration Checklist

### Files to Review Before Committing
1. **backend/provenance.db** - Should be gitignored (already is via `*.db`)
2. **backend/content/uploads/media_registry.json** - Already gitignored (in `content/`)
3. **Any test video files** - Already gitignored (via `*.mp4` patterns)
4. **Log files** - Already gitignored (via `logs/` and `*.log`)

### Files to Potentially Remove
1. **frontend/src/components/VideoRangeSelectorOld.tsx** - ✅ **NOT USED** (no imports found) - Safe to remove
2. **frontend/src/components/VideoRangeSelectorSimple.tsx** - ✅ **NOT USED** (no imports found) - Safe to remove

### Documentation Updates Needed
1. **README.md** - Already updated with new features
2. **backend/README.md** - Already updated with new endpoints
3. Consider adding `.env.example` files

---

## 🎯 Migration Plan

### Phase 1: Pre-Commit Safety Checks
1. ✅ Verify `.gitignore` is comprehensive
2. ✅ Check for any `.env` files that might be tracked
3. ✅ Review untracked files list
4. ✅ Create `.env.example` files if needed
5. ✅ Remove any unnecessary legacy files

### Phase 2: Create .env.example Files
- **frontend/.env.example**: 
  ```env
  VITE_API_BASE_URL=http://127.0.0.1:8000
  ```
- **backend/.env.example**: (Currently no required env vars, but create empty file for consistency)

### Phase 3: Clean Up Legacy Files
- ✅ Remove `VideoRangeSelectorOld.tsx` (confirmed unused - no imports)
- ✅ Remove `VideoRangeSelectorSimple.tsx` (confirmed unused - no imports)

### Phase 4: Update README
- Ensure README.md reflects all new features:
  - Media Registry & Caching
  - YouTube URL Ingestion (probe → fetch → analyze)
  - Re-analysis with media_id
  - Run History feature
  - Format selection improvements

### Phase 5: Create integrated-v2 Branch
1. Ensure we're on `integrated-dev` branch
2. Create new branch: `git checkout -b integrated-v2`
3. Stage all changes: `git add .`
4. Review staged files carefully (especially check for .env, .db, large files)
5. Commit with descriptive message
6. Push to remote: `git push origin integrated-v2`

### Phase 6: Verification
1. Check GitHub to ensure branch was created
2. Verify no sensitive files were committed
3. Test that the branch can be cloned fresh

---

## 📝 Commit Message Draft

```
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

Frontend Changes:
- Added UrlIngestForm component for YouTube URL input
- Added VideoRangeSelector for analysis window selection
- Added VirtualPreview component for browser-based previews
- Enhanced Results page with run history dropdown
- Updated Upload page with URL ingestion flow
- Added cache verification and refetch UI

Documentation:
- Updated README.md with new features and flow
- Updated backend/README.md with new endpoints
- Added architecture and QA documentation

Breaking Changes: None (backward compatible)
```

---

## ⚠️ Important Notes

1. **Never commit `.env` files** - Double-check before staging
2. **Never commit database files** - `provenance.db` should stay ignored
3. **Never commit video files** - All video patterns are gitignored
4. **Never commit logs** - Log directories are gitignored
5. **Line endings** - Git warnings about LF/CRLF are normal on Windows, but we should configure `.gitattributes` if needed

---

## 🔄 Next Steps After Approval

1. Create `.env.example` files
2. Review and remove legacy components if unused
3. Final README review
4. Create `integrated-v2` branch
5. Stage, review, and commit changes
6. Push to remote
7. Verify on GitHub

---

**Status**: ⏳ Awaiting approval to proceed

