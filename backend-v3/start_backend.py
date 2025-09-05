#!/usr/bin/env python3
"""
Startup script for backend-v3 that automatically configures FFmpeg environment.
This ensures FFmpeg is available regardless of system PATH configuration.
"""
import os
import sys
import subprocess
import platform

def setup_ffmpeg_environment():
    """Setup FFmpeg environment automatically."""
    print("🔧 Setting up FFmpeg environment...")
    
    # Get the current directory (backend-v3)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for bundled FFmpeg
    if platform.system() == "Windows":
        ffmpeg_dir = os.path.join(current_dir, "ffmpeg", "windows", "bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    elif platform.system() == "Linux":
        ffmpeg_dir = os.path.join(current_dir, "ffmpeg", "linux", "bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg")
    elif platform.system() == "Darwin":  # macOS
        ffmpeg_dir = os.path.join(current_dir, "ffmpeg", "macos", "bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg")
    else:
        print(f"⚠️  Unsupported platform: {platform.system()}")
        return False
    
    # Check if bundled FFmpeg exists
    if os.path.exists(ffmpeg_exe):
        print(f"✅ Found bundled FFmpeg: {ffmpeg_exe}")
        
        # Add to current session PATH
        current_path = os.environ.get('PATH', '')
        if ffmpeg_dir not in current_path:
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + current_path
            print(f"✅ Added bundled FFmpeg to PATH: {ffmpeg_dir}")
        
        return True
    
    # Check if system FFmpeg is available
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Found system FFmpeg")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ No FFmpeg available (neither bundled nor system)")
    print("💡 To enable full functionality:")
    print("   1. Install FFmpeg system-wide, or")
    print("   2. Ensure bundled binaries are present in ffmpeg/ directory")
    
    return False

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting Surveillance AI Backend...")
    
    # Setup FFmpeg first
    ffmpeg_available = setup_ffmpeg_environment()
    
    if ffmpeg_available:
        print("✅ FFmpeg configured successfully - full preview generation enabled")
    else:
        print("⚠️  FFmpeg not available - preview generation will be limited")
    
    print("🌐 Starting server on http://127.0.0.1:8000")
    print("📖 API documentation: http://127.0.0.1:8000/docs")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    # Start the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "app:app",
            "--host", "127.0.0.1", "--port", "8000", "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_server()
