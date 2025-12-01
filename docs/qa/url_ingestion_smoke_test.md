# YouTube URL Ingestion - QA Smoke Test

## 🧪 Test Overview

This smoke test validates the complete YouTube URL ingestion workflow from configuration to analysis and export functionality.

## 📋 Prerequisites

- Backend server running on `http://127.0.0.1:8000`
- Frontend running on `http://localhost:8080`
- `yt-dlp` dependency installed (`pip install yt-dlp`)
- FFmpeg available in system PATH

## 🔧 Test Steps

### Step 1: Enable URL Ingestion Feature

1. **Open backend configuration:**
   ```bash
   # Edit backend/config/clip_config.yaml
   ```

2. **Enable URL ingestion:**
   ```yaml
   url_ingest:
     enabled: true                    # Change from false to true
     provider: "youtube"
     max_duration_minutes: 120
     max_size_mb: 2048
     work_dir: "uploads/url_tmp"
     user_agent: "Mozilla/5.0"
     keep_hours: 24
     preferred_quality: "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4"
   ```

3. **Restart backend server:**
   ```bash
   cd backend
   uvicorn app:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Verify startup logs:**
   - Look for: `"URL ingestion enabled - YouTube URL analysis available"`
   - Check: `"URL work directory: uploads/url_tmp"`
   - Confirm: `"Max duration: 120 minutes"` and `"Max size: 2048 MB"`

### Step 2: Frontend URL Ingestion Test

1. **Navigate to upload page:**
   - Open `http://localhost:8080/upload`

2. **Switch to "From URL" tab:**
   - Click the "From URL" tab (should show ExternalLink icon)
   - Verify tab content loads with URL input form

3. **Enter test YouTube URL:**
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```
   *(Use any public YouTube video - this is just an example)*

4. **Configure rights and quality:**
   - ✅ Check "I have rights to download and analyze this content"
   - Select quality: "720p" (or "Auto")
   - Leave time window empty for full video (or set small window like `00:01:00` to `00:02:00`)

5. **Submit URL ingestion:**
   - Click "Fetch & Analyze" button
   - Verify loading state: "Fetching video from YouTube..."
   - Wait for success message: "Successfully fetched: [Video Title]"

### Step 3: Verify Time Window Selection

1. **After successful ingestion:**
   - Verify green checkmark appears: "Video loaded: [duration]"
   - Time picker should appear with video duration

2. **Set analysis window:**
   - Use range slider to select small window (e.g., 1-2 minutes)
   - Or use time pickers to set specific start/end times
   - Verify smooth slider movement and time updates

3. **Configure analysis prompts:**
   - Add prompts: "person", "car", "building"
   - Verify prompt chips appear correctly

### Step 4: Execute Analysis

1. **Start analysis:**
   - Click "Analyze Video" button (should replace "Continue" button)
   - Verify loading state: "Analyzing..."

2. **Monitor analysis progress:**
   - Check backend logs for analysis progress
   - Verify no errors in console
   - Wait for completion (typically 1-3 minutes for short clips)

3. **Verify results page:**
   - Should redirect to `/results` page
   - Check for analysis results with detections
   - Verify provenance data is displayed (title, channel, source URL)

### Step 5: Test Virtual Previews

1. **Verify virtual previews:**
   - Check that preview clips show in results
   - Click play on virtual previews
   - Verify video seeks to correct timestamps
   - Confirm video pauses at end of detection window

2. **Test preview controls:**
   - Play/pause functionality
   - Replay button
   - Verify smooth seeking within detection windows

### Step 6: Test Export-on-Demand

1. **Export a detection clip:**
   - Find a detection with export button (ExternalLink icon)
   - Click export button
   - Verify download starts automatically

2. **Verify exported file:**
   - Check downloaded MP4 file
   - Verify file plays correctly
   - Check for watermark with timestamp
   - Confirm file size is reasonable

3. **Test export API directly:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/export" \
     -H "Content-Type: application/json" \
     -d '{
       "media_id": "yt_[videoId]_[timestamp]",
       "start": "00:01:00",
       "end": "00:01:30",
       "label": "test_export"
     }'
   ```

### Step 7: Verify Cleanup System

1. **Check temp file creation:**
   ```bash
   ls -la backend/uploads/url_tmp/
   ```
   - Should see downloaded MP4 file with `yt_` prefix

2. **Check provenance database:**
   ```bash
   sqlite3 backend/provenance.db "SELECT * FROM provenance;"
   ```
   - Should see record with media_id, source_url, title, etc.

3. **Monitor cleanup logs:**
   - Wait 5+ minutes for cleanup cycle
   - Check backend logs for cleanup messages
   - Verify files are not immediately deleted (within 24-hour window)

### Step 8: Test Error Handling

1. **Test private video:**
   - Try URL: `https://www.youtube.com/watch?v=private_video_id`
   - Verify error: "This video is private. Please use a public video."

2. **Test invalid URL:**
   - Try URL: `https://example.com/not-youtube`
   - Verify error: "Invalid YouTube URL. Please provide a valid YouTube video URL."

3. **Test without rights confirmation:**
   - Uncheck rights checkbox
   - Submit form
   - Verify error: "Please confirm you have rights to download this content."

### Step 9: Disable Feature (Cleanup)

1. **Disable URL ingestion:**
   ```yaml
   # backend/config/clip_config.yaml
   url_ingest:
     enabled: false  # Change back to false
   ```

2. **Restart backend server**

3. **Verify feature is disabled:**
   - Try to submit URL form
   - Should see error: "URL ingestion is disabled. Set url_ingest.enabled=true in configuration to enable."

## ✅ Success Criteria

- [ ] URL ingestion feature enables/disables correctly
- [ ] YouTube URL downloads successfully with yt-dlp
- [ ] Time window selection works with range slider
- [ ] Analysis completes without errors
- [ ] Virtual previews play correctly with seeking
- [ ] Export-on-demand generates downloadable MP4 files
- [ ] Provenance data is tracked and displayed
- [ ] Error handling works for invalid inputs
- [ ] Cleanup system runs without errors
- [ ] Feature can be disabled cleanly

## 🐛 Common Issues

- **yt-dlp not found**: Install with `pip install yt-dlp`
- **FFmpeg errors**: Ensure FFmpeg is in system PATH
- **CORS errors**: Check frontend is running on correct port
- **File permissions**: Ensure backend has write access to `uploads/url_tmp/`
- **Network issues**: Verify internet connection for YouTube access

## 📊 Expected Performance

- **URL Ingestion**: 10-30 seconds for 1-2 minute clips
- **Analysis**: 1-3 minutes for short clips (depends on prompts)
- **Virtual Previews**: Instant loading and seeking
- **Export**: 5-15 seconds for clip generation
- **Cleanup**: Runs every 5 minutes, removes files after 24 hours
