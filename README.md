# 🎯 Surveillance AI Platform

An AI-powered video surveillance system with real-time analysis, live alerts, and a modern web interface. The platform combines a FastAPI backend with CLIP-based video analysis and a React frontend for seamless user experience.

## 🚀 Features

### Backend (FastAPI)
- **Video Analysis**: Upload videos and get detailed analysis using CLIP ViT-B/32 model
- **Natural Language Prompts**: Ask questions about video content in plain English
- **Real-time Processing**: Stream video analysis results with progress tracking
- **Live Alert System**: WebSocket-based real-time alerts with REST API
- **Export Functionality**: Generate downloadable clips and analysis reports
- **Multi-Model Support**: CLIP (primary) and Google Video Intelligence (optional)
- **GPU Acceleration**: CUDA support for faster processing

### Frontend (React + TypeScript)
- **Modern UI**: Built with React, TypeScript, and shadcn/ui components
- **Real-time Updates**: Live alert streaming via WebSocket
- **Responsive Design**: Works on desktop and mobile devices
- **File Upload**: Drag-and-drop video upload with progress tracking
- **Results Visualization**: Interactive display of analysis results
- **Export Management**: Download clips and analysis reports

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI + Uvicorn
- **AI Models**: OpenAI CLIP ViT-B/32, Google Video Intelligence API
- **Language Models**: LangChain + OpenAI/Gemini for prompt interpretation
- **Real-time**: WebSocket for live alerts
- **Deployment**: Google Colab (GPU support) or local

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: shadcn/ui + Tailwind CSS
- **State Management**: TanStack Query + React Context
- **Routing**: React Router DOM
- **Real-time**: WebSocket client

## 📁 Project Structure

```
Surveillance AI/
├── backend-v3/              # FastAPI backend
│   ├── app.py              # Main FastAPI application
│   ├── analyzer.py         # Video analysis pipeline
│   ├── prompt_interpreter.py # LangChain integration
│   ├── clip_loader.py      # CLIP model management
│   ├── frame_extractor.py  # Video frame extraction
│   ├── alert_classifier.py # Detection classification
│   ├── error_handler.py    # Error management
│   ├── colab_compat.py     # Colab compatibility
│   ├── requirements.txt    # Python dependencies
│   └── config/            # Configuration files
├── frontend/               # React frontend
│   ├── src/               # Source code
│   │   ├── components/    # UI components
│   │   ├── pages/        # Page components
│   │   ├── context/      # React contexts
│   │   ├── lib/          # Utilities and API
│   │   └── App.tsx       # Main app component
│   ├── package.json      # Node.js dependencies
│   └── vite.config.ts    # Vite configuration
├── README.md             # This file
├── .gitignore           # Git ignore rules
└── start_backend.bat    # Windows backend startup script
```

## 🚀 Quick Start

### Prerequisites
- **Backend**: Python 3.8+, pip, virtualenv
- **Frontend**: Node.js 18+, npm/yarn
- **Optional**: CUDA-capable GPU for faster processing

### Backend Setup
```bash
# Navigate to backend directory
cd backend-v3

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Environment Configuration

#### Backend Environment Variables
Create `backend-v3/.env`:
```env
OPENAI_API_KEY=your_openai_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

#### Frontend Environment Variables
Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

## 📡 API Endpoints

### Core Analysis
- `POST /analyze` - Upload and analyze video
- `GET /status?jobId={id}` - Check analysis progress
- `GET /results?jobId={id}` - Get analysis results
- `GET /health` - Health check with device info

### Export Functions
- `POST /export/clips` - Start export job
- `GET /export/status?exportId={id}` - Check export progress
- `GET /downloads/{file}` - Download exported files

### Live Alert System
- `GET /live/alerts` - Get alert history
- `POST /live/acknowledge` - Acknowledge alerts
- `POST /live/pin` - Pin/unpin alerts
- `POST /live/note` - Add notes to alerts
- `POST /live/export` - Export alert clips
- `WebSocket /ws/live` - Real-time alert streaming

### Static Files
- `GET /previews/{file}` - Preview clips and thumbnails
- `GET /downloads/{file}` - Exported files

## 🔧 Development Workflow

### Git Branch Strategy
- `main` - Clean, minimal (not used for development)
- `backend-v3.1` - Backend-only development
- `frontend-v2` - Frontend-only development

### Working on Backend
```bash
git checkout backend-v3.1
# Work on backend-v3/ files
git add backend-v3/
git commit -m "backend: new feature"
git push origin backend-v3.1
```

### Working on Frontend
```bash
git checkout frontend-v2
# Work on frontend/ files
git add frontend/
git commit -m "frontend: new component"
git push origin frontend-v2
```

### Integration Testing
1. Start backend: `cd backend-v3 && python -m uvicorn app:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open frontend at `http://localhost:3000`
4. Test video upload and analysis workflow

## 🚀 Deployment

### Backend Deployment (Google Colab)
1. Upload backend files to Google Drive
2. Open Colab notebook with GPU runtime
3. Install dependencies and start server
4. Use ngrok for public access: `!ngrok http 8000`

### Frontend Deployment
1. Build for production: `npm run build`
2. Deploy `dist/` folder to hosting service
3. Update environment variables for production API URL

## 🔍 API Documentation

- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## 🧪 Testing

### Backend Tests
```bash
cd backend-v3
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📊 Performance

- **GPU Acceleration**: Available via CUDA for faster CLIP processing
- **Real-time Streaming**: WebSocket for live alerts
- **Caching**: Model caching for faster subsequent analyses
- **Compression**: Gzip compression for API responses

## 🔐 Security

- **CORS**: Configured for specific origins
- **File Validation**: Video file type and size validation
- **Error Handling**: Comprehensive error responses without sensitive data
- **Environment Variables**: Secure API key management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the logs in `backend-v3/content/logs/`
3. Test with the provided example videos
4. Open an issue on GitHub

---

**Ready for production use with proper environment configuration and deployment setup!**
