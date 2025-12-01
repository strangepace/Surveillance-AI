# URL Ingestion Testing Examples

## Test Examples for POST /ingest/url

### 1. Auto Format Selection (No format_id)

```bash
curl -X POST "http://127.0.0.1:8000/ingest/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=SK7yB7EtMkk",
    "start": "00:01:00",
    "end": "00:02:00",
    "rights_confirmed": true
  }'
```

**Expected Response:**
```json
{
  "media_id": "yt_SK7yB7EtMkk_1694567890",
  "title": "Avunanavaa - Tamil Song",
  "duration": 60.0,
  "original_url": "http://127.0.0.1:8000/uploads/url_tmp/yt_SK7yB7EtMkk_1694567890.mp4",
  "window": {
    "start": "00:01:00",
    "end": "00:02:00",
    "offsetSeconds": 60.0
  },
  "format_used": "137+140",
  "codec_info": {
    "vcodec": "h264",
    "acodec": "aac"
  }
}
```

### 2. Explicit Format Selection (Video+Audio Merge)

```bash
curl -X POST "http://127.0.0.1:8000/ingest/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=SK7yB7EtMkk",
    "start": "00:01:00",
    "end": "00:02:00",
    "rights_confirmed": true,
    "format_id": "137+140"
  }'
```

**Expected Response:**
```json
{
  "media_id": "yt_SK7yB7EtMkk_1694567891",
  "title": "Avunanavaa - Tamil Song",
  "duration": 60.0,
  "original_url": "http://127.0.0.1:8000/uploads/url_tmp/yt_SK7yB7EtMkk_1694567891.mp4",
  "window": {
    "start": "00:01:00",
    "end": "00:02:00",
    "offsetSeconds": 60.0
  },
  "format_used": "137+140",
  "codec_info": {
    "vcodec": "h264",
    "acodec": "aac"
  }
}
```

### 3. Single Format Selection

```bash
curl -X POST "http://127.0.0.1:8000/ingest/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=SK7yB7EtMkk",
    "start": "00:01:00",
    "end": "00:02:00",
    "rights_confirmed": true,
    "format_id": "18"
  }'
```

### 4. Full Video Download (No time window)

```bash
curl -X POST "http://127.0.0.1:8000/ingest/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=SK7yB7EtMkk",
    "rights_confirmed": true,
    "format_id": "137+140"
  }'
```

## Format Inspection Examples

### Get Available Formats

```bash
curl "http://127.0.0.1:8000/ingest/url/formats?url=https://www.youtube.com/watch?v=SK7yB7EtMkk"
```

**Expected Response:**
```json
{
  "formats": [
    {
      "format_id": "auto",
      "vcodec": "avc1.4d401f",
      "acodec": "mp4a.40.2",
      "ext": "mp4",
      "resolution": "1280x720",
      "height": 720,
      "fps": 30,
      "filesize": 45678901,
      "note": "av",
      "recommended": true,
      "warning": null
    },
    {
      "format_id": "137+140",
      "vcodec": "avc1.4d401f",
      "acodec": "mp4a.40.2",
      "ext": "mp4",
      "resolution": "1280x720",
      "height": 720,
      "fps": 30,
      "filesize": 45678901,
      "note": "av",
      "recommended": true,
      "warning": null
    },
    {
      "format_id": "136+140",
      "vcodec": "avc1.4d401e",
      "acodec": "mp4a.40.2",
      "ext": "mp4",
      "resolution": "854x480",
      "height": 480,
      "fps": 30,
      "filesize": 23456789,
      "note": "av",
      "recommended": true,
      "warning": null
    }
  ]
}
```

## Error Cases

### 1. Missing Rights Confirmation

```bash
curl -X POST "http://127.0.0.1:8000/ingest/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=SK7yB7EtMkk",
    "rights_confirmed": false
  }'
```

**Expected Response:**
```json
{
  "detail": "Rights confirmation required. You must confirm you have rights to download and analyze this content."
}
```

### 2. Invalid YouTube URL

```bash
curl -X POST "http://127.0.0.1:8000/ingest/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/video",
    "rights_confirmed": true
  }'
```

**Expected Response:**
```json
{
  "detail": "Invalid YouTube URL. Please provide a valid YouTube video URL."
}
```

### 3. URL Ingestion Disabled

```bash
# First disable in config, then test
curl -X POST "http://127.0.0.1:8000/ingest/url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=SK7yB7EtMkk",
    "rights_confirmed": true
  }'
```

**Expected Response:**
```json
{
  "detail": "URL ingestion is disabled. Set url_ingest.enabled=true in configuration to enable."
}
```

## Testing Workflow

1. **Start the backend server:**
   ```bash
   cd backend
   python start_backend.py
   ```

2. **Test format inspection:**
   ```bash
   curl "http://127.0.0.1:8000/ingest/url/formats?url=https://www.youtube.com/watch?v=SK7yB7EtMkk"
   ```

3. **Test auto format selection:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/ingest/url" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=SK7yB7EtMkk", "rights_confirmed": true}'
   ```

4. **Test explicit format selection:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/ingest/url" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=SK7yB7EtMkk", "rights_confirmed": true, "format_id": "137+140"}'
   ```

5. **Verify the downloaded file:**
   ```bash
   # Check if file exists and is browser-safe
   ls -la content/uploads/url_tmp/
   ffprobe content/uploads/url_tmp/yt_*.mp4
   ```
