# 🚀 Deployment Guide - Surveillance AI Backend

## 🌟 **Cross-Platform Compatibility**

This backend is designed to work **anywhere** without manual FFmpeg installation or PATH configuration.

## 📁 **Project Structure**

```
backend-v3/
├── ffmpeg/                    # Bundled FFmpeg binaries
│   ├── windows/bin/          # Windows executables
│   ├── linux/bin/            # Linux executables
│   └── macos/bin/            # macOS executables
├── start_backend.py          # Python startup script
├── start_backend.bat         # Windows batch file
├── app.py                    # Main FastAPI application
├── utils/ffmpeg.py           # FFmpeg utility module
└── DEPLOYMENT.md             # This file
```

## 🚀 **Starting the Backend**

### **Option 1: Python Script (Recommended)**
```bash
cd backend-v3
python start_backend.py
```

### **Option 2: Windows Batch File**
```bash
cd backend-v3
start_backend.bat
```

### **Option 3: Direct Uvicorn (Legacy)**
```bash
cd backend-v3
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## 🔧 **How It Works**

1. **Automatic Detection**: Script detects your operating system
2. **Bundled Binaries**: Uses FFmpeg from the `ffmpeg/` directory
3. **PATH Configuration**: Automatically adds FFmpeg to session PATH
4. **Fallback Support**: Falls back to system FFmpeg if available
5. **Zero Configuration**: No manual setup required

## 🌍 **Platform Support**

### **Windows**
- ✅ **Bundled**: `ffmpeg/windows/bin/ffmpeg.exe`
- ✅ **System**: Any FFmpeg in system PATH
- ✅ **Auto-start**: `start_backend.bat`

### **Linux**
- ✅ **Bundled**: `ffmpeg/linux/bin/ffmpeg`
- ✅ **System**: `apt install ffmpeg` or equivalent
- ✅ **Auto-start**: `python start_backend.py`

### **macOS**
- ✅ **Bundled**: `ffmpeg/macos/bin/ffmpeg`
- ✅ **System**: `brew install ffmpeg`
- ✅ **Auto-start**: `python start_backend.py`

## 📦 **Deployment Scenarios**

### **Local Development**
```bash
git clone <your-repo>
cd backend-v3
python start_backend.py
```

### **Production Server**
```bash
# Copy project to server
scp -r backend-v3 user@server:/opt/
ssh user@server
cd /opt/backend-v3
python start_backend.py
```

### **Docker Container**
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app/backend-v3
RUN pip install -r requirements.txt
CMD ["python", "start_backend.py"]
```

### **Cloud Deployment**
- **AWS EC2**: Copy project, run `python start_backend.py`
- **Google Cloud**: Same as EC2
- **Azure**: Same as EC2
- **Heroku**: Use `start_backend.py` as Procfile command

## 🔍 **Troubleshooting**

### **FFmpeg Not Found**
```bash
# Check bundled binaries
ls ffmpeg/windows/bin/  # Windows
ls ffmpeg/linux/bin/    # Linux
ls ffmpeg/macos/bin/    # macOS

# Check system FFmpeg
ffmpeg -version
```

### **Permission Issues**
```bash
# Make executable (Linux/macOS)
chmod +x ffmpeg/linux/bin/ffmpeg
chmod +x ffmpeg/macos/bin/ffmpeg
```

### **Python Dependencies**
```bash
pip install -r requirements.txt
```

## 📋 **Deployment Checklist**

- ✅ **Project copied** to target system
- ✅ **Python 3.8+** installed
- ✅ **Dependencies** installed (`pip install -r requirements.txt`)
- ✅ **FFmpeg binaries** present in `ffmpeg/` directory
- ✅ **Start script** executable (`python start_backend.py`)

## 🌟 **Benefits of This Approach**

1. **Zero Configuration**: Works out of the box
2. **Cross-Platform**: Windows, Linux, macOS
3. **Portable**: Copy and run anywhere
4. **No Dependencies**: FFmpeg included
5. **Professional**: Ready for production deployment

## 🚀 **Quick Start**

```bash
# 1. Clone/copy project
git clone <your-repo>
cd backend-v3

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start backend
python start_backend.py

# 4. Access API
# Frontend: http://localhost:8080
# Backend: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**That's it! No manual FFmpeg installation, no PATH configuration, no platform-specific setup.** 🎉
