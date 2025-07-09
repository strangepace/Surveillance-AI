# 🚀 Surveillance AI - Quick Start Guide

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **API Keys**:
   - OpenAI API key (for GPT-3.5-turbo)
   - Google Gemini API key
   - Google Cloud credentials (for Video Intelligence API)

## 🔧 Local Setup

### 1. Environment Setup
```bash
# Run the setup script
python setup_local.py

# Create .env file (copy from env_template.txt)
cp env_template.txt .env
# Edit .env with your actual API keys
```

### 2. Google Cloud Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Video Intelligence API**
4. Create a **Service Account** with Video Intelligence permissions
5. Download `credentials.json` and place in project root

### 3. Start the Server
```bash
python main.py
```

The server will start at `http://localhost:8000`

## 🌐 Google Colab Setup (Recommended for GPU)

### 1. Upload Files to Google Drive
Upload all project files to a folder called `surveillance-ai` in your Google Drive.

### 2. Open the Notebook
Open `surveillance_ai_colab.ipynb` in Google Colab.

### 3. Set Runtime
- Go to **Runtime → Change runtime type**
- Set **Hardware accelerator** to **GPU**

### 4. Run All Cells
Execute all cells in order. The server will start automatically.

## 📡 API Usage

### Upload and Analyze Video
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "video=@your_video.mp4" \
  -F "prompt=What objects are visible in this video?" \
  -F "model=chatgpt"
```

### Available Models
- `chatgpt` - Uses OpenAI GPT-3.5-turbo
- `gemini` - Uses Google Gemini Pro

### Example Prompts
- "What objects are visible in this video?"
- "Are there any people in the video?"
- "What activities are happening?"
- "Is there any suspicious activity?"

## 📁 Project Structure

```
Surveillance AI/
├── main.py                 # FastAPI server
├── routes.py              # API endpoints
├── video_processor.py     # Google Video Intelligence integration
├── prompt_interpreter.py  # LangChain + OpenAI/Gemini
├── event_matcher.py       # Event detection logic
├── logger.py             # Logging system
├── colab_setup.py        # Google Colab setup
├── surveillance_ai_colab.ipynb  # Colab notebook
├── requirements.txt      # Python dependencies
├── .env                 # API keys (create this)
├── credentials.json     # Google Cloud credentials
└── content/
    ├── uploads/         # Uploaded videos
    └── logs/           # Analysis logs
```

## 🔍 Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Ensure `.env` file exists with valid API keys
   - Check that `credentials.json` is in project root

2. **Import Errors**
   - Run `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

3. **Google Cloud Errors**
   - Verify Video Intelligence API is enabled
   - Check service account permissions
   - Ensure `credentials.json` is valid

4. **Video Processing Errors**
   - Check video file format (MP4 recommended)
   - Ensure video file is not corrupted
   - Check file size (Google Cloud has limits)

### Getting Help

1. Check the logs in `content/logs/`
2. Review the API documentation at `http://localhost:8000/docs`
3. Test with the health endpoint: `http://localhost:8000/health`

## 🎯 Next Steps

Once you're up and running:

1. **Test with sample videos** in `content/uploads/`
2. **Experiment with different prompts** and models
3. **Review analysis logs** to understand the system
4. **Customize the prompt templates** in `prompt_interpreter.py`
5. **Add new video processing features** as needed

## 📊 Performance Tips

- **Use Google Colab** for GPU acceleration
- **Optimize video size** before upload
- **Use specific prompts** for better results
- **Monitor API usage** to manage costs 