# 🎯 Surveillance AI Platform

An AI-powered video surveillance system that analyzes uploaded videos and answers natural language questions about the content using Google Video Intelligence API, OpenAI GPT-3.5-turbo, and Google Gemini.

## 🚀 Features

- **Video Analysis**: Upload videos and get detailed analysis of objects, people, and activities
- **Natural Language Queries**: Ask questions about video content in plain English
- **Multi-Model Support**: Choose between OpenAI GPT-3.5-turbo and Google Gemini
- **Google Colab Integration**: GPU-accelerated processing for faster analysis
- **RESTful API**: FastAPI backend with automatic documentation
- **Real-time Processing**: Stream video analysis results

## 🛠️ Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Video Analysis**: Google Cloud Video Intelligence API
- **AI Models**: OpenAI GPT-3.5-turbo, Google Gemini Pro
- **Framework**: LangChain for AI orchestration
- **Deployment**: Google Colab (GPU support)
- **Documentation**: Auto-generated API docs

## 📁 Project Structure

```
Surveillance AI/
├── main.py                 # FastAPI server entry point
├── routes.py              # API endpoints
├── video_processor.py     # Google Video Intelligence integration
├── prompt_interpreter.py  # LangChain + OpenAI/Gemini
├── event_matcher.py       # Event detection logic
├── logger.py             # Logging system
├── colab_setup.py        # Google Colab setup script
├── surveillance_ai_colab.ipynb  # Colab notebook
├── setup_local.py        # Local development setup
├── requirements.txt      # Python dependencies
├── QUICK_START.md       # Setup guide
├── env_template.txt      # Environment variables template
└── content/
    ├── uploads/         # Uploaded videos
    └── logs/           # Analysis logs
```

## 🚀 Quick Start

See [QUICK_START.md](QUICK_START.md) for detailed setup instructions.

### Local Development
```bash
# Setup environment
python setup_local.py

# Start server
python main.py
```

### Google Colab (Recommended)
1. Upload files to Google Drive
2. Open `surveillance_ai_colab.ipynb`
3. Set runtime to GPU
4. Run all cells

## 📡 API Usage

### Analyze Video
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "video=@your_video.mp4" \
  -F "prompt=What objects are visible in this video?" \
  -F "model=chatgpt"
```

### Available Models
- `chatgpt` - OpenAI GPT-3.5-turbo
- `gemini` - Google Gemini Pro

### Example Prompts
- "What objects are visible in this video?"
- "Are there any people in the video?"
- "What activities are happening?"
- "Is there any suspicious activity?"

## 🔧 Configuration

### Environment Variables
Create a `.env` file with:
```
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
```

### Google Cloud Setup
1. Enable Video Intelligence API
2. Create service account
3. Download `credentials.json`

## 📊 Performance

- **GPU Acceleration**: Available via Google Colab
- **Batch Processing**: Support for multiple video formats
- **Real-time Analysis**: Stream processing capabilities
- **Cost Optimization**: Efficient API usage patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- Check [QUICK_START.md](QUICK_START.md) for setup help
- Review API docs at `http://localhost:8000/docs`
- Check logs in `content/logs/`
