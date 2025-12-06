# Branching & Versioning Strategy

**Last Updated:** January 2025  
**Current Branch:** `integrated-v2`

---

## 🌿 Branch Strategy Overview

### Core Branching Model

**`integrated-dev`** = **Main development branch**
- Always the latest code
- Always ahead of stable branches
- Source of truth for ongoing development
- All feature branches merge here

**`integrated-v1`, `integrated-v2`, `integrated-v3`, ...** = **Frozen stable snapshots**
- Created **from** `integrated-dev` when milestones are completed
- Frozen at the point of creation (no new development)
- Used for production deployments and stable releases
- Only modified for rare emergency hotfixes

**`feature/*`** = Feature branches
- All new development happens here
- Must merge back into `integrated-dev` when complete

**`hotfix/*`** = Urgent bug fixes
- Can be applied directly to stable branches if needed
- If applied to stable branch, must also be merged into `integrated-dev`

---

## 📋 Workflow for Different Types of Changes

### 🎯 Small Features / Incremental Updates

**Scenario:** Add a new endpoint, fix a bug, improve UI, add a small feature

**Recommended Workflow:**
```bash
# 1. Always start from integrated-dev
git checkout integrated-dev
git pull origin integrated-dev

# 2. Create a feature branch
git checkout -b feature/add-export-endpoint
# or
git checkout -b bugfix/fix-preview-seek
# or
git checkout -b hotfix/critical-memory-leak

# 3. Make your changes, commit
git add .
git commit -m "feat: add export endpoint for clips"

# 4. Push feature branch
git push origin feature/add-export-endpoint

# 5. Create Pull Request to integrated-dev (or merge directly if you have access)
# After PR approval/merge, delete feature branch
```

**Version Update:**
- **Backend:** Update `backend/app.py` version from `3.1.0` → `3.1.1` (patch) or `3.2.0` (minor feature)
- **Frontend:** Update `frontend/package.json` version from `2.2.0` → `2.2.1` (patch) or `2.3.0` (minor feature)

### 🚀 Major Features / Breaking Changes

**Scenario:** Complete new feature set, architectural changes, major refactoring

**Recommended Workflow:**
```bash
# 1. Start from integrated-dev
git checkout integrated-dev
git pull origin integrated-dev

# 2. Create feature branch
git checkout -b feature/live-feed-backend-integration

# 3. Develop feature, commit regularly
git add .
git commit -m "feat: implement live feed backend processing"

# 4. When feature is complete, merge to integrated-dev
git checkout integrated-dev
git merge feature/live-feed-backend-integration
git push origin integrated-dev

# 5. When milestone is complete, create frozen snapshot branch
git checkout integrated-dev
git checkout -b integrated-v3
# Update version numbers, CHANGELOG, tag release
git push origin integrated-v3
# Note: integrated-v3 is now frozen. Continue development in integrated-dev.
```

**Version Update:**
- **Backend:** Update to `3.2.0` (minor) or `4.0.0` (major/breaking)
- **Frontend:** Update to `0.2.0` (minor) or `1.0.0` (major)

---

## 📊 Semantic Versioning Guide

### Version Number Format: `MAJOR.MINOR.PATCH`

#### Backend (`backend/app.py`)
```python
# Current: version="3.1.0"

# Patch (bug fixes, small improvements)
3.1.0 → 3.1.1  # Fixed memory leak
3.1.1 → 3.1.2  # Fixed preview generation bug

# Minor (new features, backward compatible)
3.1.0 → 3.2.0  # Added new export endpoint
3.2.0 → 3.3.0  # Added facial recognition

# Major (breaking changes, major features)
3.1.0 → 4.0.0  # Complete architecture overhaul
4.0.0 → 5.0.0  # New API structure
```

#### Frontend (`frontend/package.json`)
```json
// Current: "version": "2.2.0"
// (frontend-v2 was 2.0.0, integrated-v1/v2 added: hybrid preview, YouTube, re-analysis)

// Patch (bug fixes, small improvements)
"2.2.0" → "2.2.1"  // Fixed UI bug
"2.2.1" → "2.2.2"  // Fixed preview issue

// Minor (new features, backward compatible)
"2.2.0" → "2.3.0"  // Added new UI feature
"2.3.0" → "2.4.0"  // Added export functionality

// Major (breaking changes, major features)
"2.2.0" → "3.0.0"  // Complete UI overhaul
"3.0.0" → "4.0.0"  // New architecture
```

---

## 🔄 Recommended Development Workflow

### Daily Development (Small Changes)

```bash
# 1. Always start from integrated-dev
git checkout integrated-dev
git pull origin integrated-dev

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes, commit
git add .
git commit -m "feat: description of change"

# 4. Push and create PR (or merge if you have direct access)
git push origin feature/your-feature-name

# 5. After merge, update version if needed
# Then delete local branch
git checkout integrated-dev
git branch -d feature/your-feature-name
```

### Feature Development (Medium Changes)

```bash
# Same as above, but:
# - Update version number (minor: 3.1.0 → 3.2.0)
# - Add to CHANGELOG.md
# - Update documentation if needed
```

### Major Release (Large Changes)

```bash
# 1. Complete all features in integrated-dev
# 2. Test thoroughly
# 3. Create new major branch
git checkout integrated-dev
git checkout -b integrated-v3

# 4. Update version numbers
# Backend: 3.1.0 → 4.0.0 (or 3.2.0 if not breaking)
# Frontend: 0.0.0 → 0.2.0 (or 1.0.0 if stable)

# 5. Update CHANGELOG.md with release notes
# 6. Tag the release
git tag -a v3.0.0 -m "Release v3.0.0: Major features"
git push origin integrated-v3
git push origin v3.0.0
```

---

## 📝 Version Update Checklist

### For Small Changes (Patch)
- [ ] Update `backend/app.py` version: `3.1.0` → `3.1.1`
- [ ] Update `frontend/package.json` version: `0.0.0` → `0.0.1` (or keep if very minor)
- [ ] Add entry to CHANGELOG.md (optional for patches)

### For New Features (Minor)
- [ ] Update `backend/app.py` version: `3.1.0` → `3.2.0`
- [ ] Update `frontend/package.json` version: `0.0.0` → `0.1.0`
- [ ] Add entry to CHANGELOG.md
- [ ] Update relevant documentation

### For Major Releases
- [ ] Update `backend/app.py` version: `3.1.0` → `4.0.0`
- [ ] Update `frontend/package.json` version: `0.0.0` → `1.0.0`
- [ ] Create comprehensive CHANGELOG.md entry
- [ ] Update all documentation
- [ ] Create release branch (`integrated-v3`)
- [ ] Tag the release

---

## 🎯 Branch Naming Conventions

### Feature Branches
```
feature/add-export-endpoint
feature/live-feed-backend
feature/facial-recognition
feature/ui-improvements
```

### Bug Fix Branches
```
bugfix/fix-preview-seek
bugfix/memory-leak-export
bugfix/youtube-download-error
```

### Hotfix Branches (Urgent)
```
hotfix/critical-security-fix
hotfix/api-crash-fix
hotfix/data-loss-prevention
```

---

## 📋 Example Scenarios

### Scenario 1: Add a Small Feature
**Task:** Add a "Download All" button to results page

```bash
git checkout integrated-dev
git checkout -b feature/download-all-button
# Make changes
git commit -m "feat: add download all button to results page"
git push origin feature/download-all-button
# Create PR → merge to integrated-dev
# Update version: 3.1.0 → 3.1.1 (or 3.2.0 if significant)
```

### Scenario 2: Fix a Bug
**Task:** Fix preview video not seeking correctly

```bash
git checkout integrated-dev
git checkout -b bugfix/fix-preview-seek
# Fix the bug
git commit -m "fix: correct video seek behavior in VirtualPreview"
git push origin bugfix/fix-preview-seek
# Create PR → merge to integrated-dev
# Update version: 3.1.0 → 3.1.1
```

### Scenario 3: Major Feature
**Task:** Complete live feed backend integration

```bash
git checkout integrated-dev
git checkout -b feature/live-feed-backend
# Develop feature (may take days/weeks)
git commit -m "feat: implement live feed processing backend"
# ... more commits ...
git push origin feature/live-feed-backend
# Create PR → merge to integrated-dev
# When ready, create integrated-v3 branch
git checkout integrated-dev
git checkout -b integrated-v3
# Update versions: 3.1.0 → 3.2.0 (or 4.0.0 if breaking)
```

---

## 🔗 Branch Relationships

```
main (baseline, unchanged)
  │
  ├── integrated-v1 (frozen snapshot)
  │
  ├── integrated-v2 (frozen snapshot) ✅
  │
  └── integrated-dev (main development, always ahead)
        │
        ├── feature/add-export-endpoint → merge to integrated-dev
        ├── feature/live-feed-backend → merge to integrated-dev
        ├── bugfix/fix-preview-seek → merge to integrated-dev
        └── hotfix/critical-fix → merge to integrated-dev (and stable branch if urgent)
```

**Development Flow:**
1. **All features** → Developed in `feature/*` branches
2. **Feature complete** → Merge into `integrated-dev`
3. **Milestone reached** → Create frozen snapshot `integrated-v3` from `integrated-dev`
4. **Continue development** → Keep working in `integrated-dev` (it moves forward independently)

**Critical Rules:**
- ✅ `integrated-dev` is always the source of truth and moves forward independently
- ✅ `integrated-vX` branches are **frozen snapshots** - do NOT merge them back into `integrated-dev`
- ⚠️ **Exception:** If a hotfix is applied directly to a stable branch, it must also be merged into `integrated-dev`
- ✅ New stable branches are created **from** `integrated-dev` when milestones are complete

---

## ✅ Best Practices

1. **Always branch from `integrated-dev`** for new work
2. **Update version numbers** when merging features
3. **Keep feature branches small** - one feature per branch
4. **Delete branches** after merging
5. **Use descriptive commit messages** - `feat:`, `fix:`, `docs:`, etc.
6. **Create PRs** for code review (if working in team)
7. **Tag releases** on major branches
8. **Update CHANGELOG.md** for user-facing changes

---

## 📝 Quick Reference

### Small Update Workflow
```bash
git checkout integrated-dev && git pull
git checkout -b feature/your-feature
# Make changes
git commit -m "feat: your feature"
git push origin feature/your-feature
# Merge to integrated-dev
# Update version (patch or minor)
```

### Major Release Workflow (Creating Stable Snapshot)
```bash
# 1. Ensure all features are merged to integrated-dev
# 2. Test thoroughly
# 3. Create frozen snapshot branch from integrated-dev
git checkout integrated-dev
git checkout -b integrated-v3

# 4. Update version numbers, CHANGELOG, docs
git commit -m "chore: prepare v3.0.0 release"

# 5. Tag the release
git tag -a v3.0.0 -m "Release v3.0.0: Major features"
git push origin integrated-v3
git push origin v3.0.0

# 6. Return to integrated-dev and continue development
git checkout integrated-dev
# integrated-v3 is now frozen. Continue new work in integrated-dev.
```

**Note:** `integrated-v3` is a frozen snapshot. Do NOT merge it back into `integrated-dev`. Development continues forward in `integrated-dev`.

---

---

## 🚨 Critical Branching Rules

1. **`integrated-dev` is the main development branch** - always the latest, always ahead
2. **`integrated-vX` branches are frozen snapshots** - created from `integrated-dev` at milestones
3. **Do NOT merge `integrated-vX` back into `integrated-dev`** (except when a hotfix was applied to stable branch)
4. **All features** must be developed in `feature/*` branches and merged into `integrated-dev`
5. **Development always moves forward** only on `integrated-dev`
6. **Create new stable branches** (`integrated-v3`, `integrated-v4`, etc.) ONLY when a milestone is fully complete

---

## 🤖 Git Workflow Assistant Role

As your Git workflow assistant, I will:

### When Work is Complete
- **Remind you to:**
  1. Save all files and run tests if available
  2. Run `git status` and, if there are changes, `git add`, `git commit` with a clear message, and `git push` to the current branch

### When Feature Branch is Stable
- **Remind you to:**
  - Merge the feature branch back into `integrated-dev` and push

### When Milestone is Reached
- **Remind you to:**
  - Create a new snapshot branch from `integrated-dev` named `integrated-v<next number>` and push it
  - Example: "FAISS + cached re-analysis complete and tested" → create `integrated-v3`

### When Coding for a While
- **Gently nudge you to:**
  - Commit/push and sync branches following these rules if there are many changes and no recent push

---

**Summary:** `integrated-dev` is the source of truth and moves forward independently. Stable branches (`integrated-v1`, `integrated-v2`, etc.) are frozen snapshots for production use. All new development happens in `feature/*` branches that merge into `integrated-dev`.

