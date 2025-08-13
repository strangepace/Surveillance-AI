# Surveillance AI — Backend-v3

## Overview
Surveillance AI backend-v3 is a FastAPI-powered video analysis system designed for intelligent surveillance, event detection, and prompt-based video search. It processes uploaded videos, interprets natural language prompts, and returns structured detection results with preview clips.

---

## Features
- REST API for video analysis and health checks
- Natural language prompt interpreter (with fallback mode)
- **CLIP ViT-B/32 model for semantic video analysis**
- Frame extraction and preview clip generation
- Structured JSON results for detections
- Robust error handling and logging
- Ready for frontend integration

---

## Model: OpenAI CLIP ViT-B/32
This backend uses the [OpenAI CLIP ViT-B/32](https://github.com/openai/CLIP) model for semantic video analysis:
- **Purpose:** Matches video frames to natural language prompts for flexible, zero-shot detection.
- **Configuration:**
  - Model name: `ViT-B/32`
  - Configurable in `config/clip_config.yaml`
  - Used in `analyzer.py` and related modules
- **Fallback:** If CLIP is unavailable, a simple analyzer is used for demo/testing.
- **Notes:**
  - Ensure the model weights are available or downloaded as needed.
  - GPU acceleration is recommended for large-scale analysis.

---

## Requirements
- Python 3.8+
- pip (Python package manager)
- Recommended: virtualenv

### Python Dependencies
Install with:
```sh
pip install -r requirements.txt
```

---

## Setup & Running the Server
1. **Navigate to backend-v3 directory:**
   ```sh
   cd backend-v3
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Start the FastAPI server:**
   ```sh
   python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
   ```
4. **Access API docs:**
   - Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## API Endpoints
### 1. Health Check
- **GET** `/health`
- Returns: `{ "status": "ok", "version": "v3" }`

### 2. Video Analysis
- **POST** `/analyze`
- **Request:**
  - `file`: Video file (mp4)
  - `prompts`: Comma-separated string (e.g., `"person, car, fire"`)
- **Response:**
  - JSON with detection results, preview clips, and metadata

---

## Example Usage
### Using Python `requests`
```python
import requests
files = {'file': open('content/uploads/naani.mp4', 'rb')}
data = {'prompts': 'elderly man, red shirt, car'}
response = requests.post('http://localhost:8000/analyze', files=files, data=data)
print(response.json())
```

### Using Swagger UI
- Go to `/docs`, use the "Try it out" button for `/analyze`.

---

## Project Structure
```
backend-v3/
├── app.py                # FastAPI app
├── analyzer.py           # Main analyzer logic
├── analyzer_simple.py    # Simple analyzer (no CLIP)
├── frame_extractor.py    # Frame extraction
├── prompt_interpreter.py # Prompt interpreter
├── clip_generator.py     # Preview clip generation
├── config/               # Config files
├── content/uploads/      # Video uploads
├── results/              # Output JSONs & previews
├── test_api_requests.py  # API test script
├── ...
```

---

## Testing
- Run `test_api_requests.py` for API tests.
- Use `/health` and `/analyze` endpoints for manual or automated tests.

---

## Troubleshooting
- **Import/module errors:** Always run the server from inside `backend-v3`.
- **Server not responding:** Check terminal for errors, ensure dependencies are installed.
- **Large file errors:** Check system memory and logs for crash details.
- **Logs:** All analysis and errors are printed to the terminal.

---

## Security & Best Practices
- Store API keys and credentials in `.env` (not in code).
- Do not commit large video files or sensitive data.
- Use `.gitignore` to keep the repo clean.

---

## License
MIT License (or your project license here) 