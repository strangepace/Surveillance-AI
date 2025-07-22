import os
import subprocess
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def mount_google_drive():
    """Mount Google Drive for persistent storage."""
    try:
        from google.colab import drive
        drive.mount('/content/drive')
        logger.info("Google Drive mounted successfully")
        return True
    except ImportError:
        logger.warning("Not running in Google Colab, skipping Drive mount")
        return False

def install_dependencies():
    """Install required packages for GPU support."""
    packages = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-multipart==0.0.6",
        "langchain==0.0.267",
        "langchain-community==0.0.10",
        "openai==1.3.5",
        "google-cloud-videointelligence==2.11.1",
        "python-dotenv==1.0.0",
        "opencv-python==4.8.1.78",
        "pydantic==1.10.13",
        "python-jose==3.3.0",
        "passlib==1.7.4",
        "bcrypt==4.0.1",
        "pytest==7.4.3",
        "httpx==0.25.2",
        "google-generativeai==0.3.2"
    ]
    
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    logger.info("Dependencies installed successfully")

def create_directories():
    """Create necessary directories for the project."""
    directories = [
        "content/uploads",
        "content/logs"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def setup_environment():
    """Set up the environment variables."""
    env_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": "/content/drive/MyDrive/surveillance-ai/credentials.json",
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "")
    }
    
    for key, value in env_vars.items():
        if not value:
            logger.warning(f"Environment variable {key} not set")
        else:
            os.environ[key] = value
            logger.info(f"Set environment variable: {key}")

def main():
    """Main setup function."""
    logger.info("Starting Colab setup...")
    
    # Mount Google Drive
    if mount_google_drive():
        # Create project directory in Drive
        project_dir = Path("/content/drive/MyDrive/surveillance-ai")
        project_dir.mkdir(exist_ok=True)
        
        # Copy project files to Drive
        current_dir = Path.cwd()
        for file in current_dir.glob("*"):
            if file.is_file() and file.name != "colab_setup.py":
                subprocess.run(["cp", str(file), str(project_dir)])
    
    # Install dependencies
    install_dependencies()
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment()
    
    logger.info("Colab setup completed successfully!")

if __name__ == "__main__":
    main() 