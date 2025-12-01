# Pre-Push Checklist for integrated-v2

## ✅ Items to Address Before Pushing

### 1. **Add `*.db` to `.gitignore`** ⚠️ CRITICAL
- **Issue**: `provenance.db` is currently NOT being ignored (git check-ignore returned nothing)
- **Fix**: Add `*.db` to `.gitignore` to ensure database files are never committed
- **Status**: ⏳ Needs to be done

### 2. **Clean Up Debug Console Logs** 📝
- **Issue**: Debug `console.log` statements in `frontend/src/lib/api.ts` (lines 54-57)
- **Fix**: Remove or comment out debug logs for production
- **Status**: ⏳ Needs to be done

### 3. **Verify `.env.example` Files** ✅
- **Status**: `frontend/.env.example` already exists and is tracked
- **Action**: Verify content is correct (should contain `VITE_API_BASE_URL=http://127.0.0.1:8000`)
- **Backend**: Check if we need `backend/.env.example` (currently no required env vars)

### 4. **Remove Legacy Components** 🗑️
- **Files**: 
  - `frontend/src/components/VideoRangeSelectorOld.tsx` (unused)
  - `frontend/src/components/VideoRangeSelectorSimple.tsx` (unused)
- **Status**: ⏳ Needs to be done

### 5. **Final Verification** ✅
- [ ] No `.env` files will be committed
- [ ] No `.db` files will be committed (after adding to .gitignore)
- [ ] No video files will be committed
- [ ] No log files will be committed
- [ ] All sensitive data is excluded

---

## 📋 Summary of Actions Needed

1. **Update `.gitignore`**: Add `*.db` pattern
2. **Clean up `api.ts`**: Remove/comment debug console.logs
3. **Remove legacy components**: Delete unused VideoRangeSelector variants
4. **Create backend/.env.example**: (optional, for consistency)
5. **Final git status check**: Verify nothing sensitive is staged

---

## 🚀 After These Fixes, We Can Proceed With:

1. Create `integrated-v2` branch
2. Stage all changes
3. Review staged files one final time
4. Commit with descriptive message
5. Push to remote
6. Verify on GitHub

---

**Status**: ⏳ Ready to fix these items, then proceed to GitHub push

