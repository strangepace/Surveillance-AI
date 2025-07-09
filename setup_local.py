#!/usr/bin/env python3
"""
Local Development Setup Script for Surveillance AI
Run this script to set up your local development environment.
"""

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

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required packages."""
    try:
        logger.info("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    directories = ["content/uploads", "content/logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"✅ Created directory: {directory}")

def check_environment_files():
    """Check if required environment files exist."""
    required_files = {
        ".env": "Environment variables file",
        "credentials.json": "Google Cloud credentials"
    }
    
    missing_files = []
    for file, description in required_files.items():
        if os.path.exists(file):
            logger.info(f"✅ {file} ({description}) found")
        else:
            logger.warning(f"❌ {file} ({description}) missing")
            missing_files.append(file)
    
    if missing_files:
        logger.warning("\n⚠️  Missing files detected:")
        for file in missing_files:
            if file == ".env":
                logger.warning("  - Create .env file with your API keys (see env_template.txt)")
            elif file == "credentials.json":
                logger.warning("  - Download credentials.json from Google Cloud Console")
        return False
    
    return True

def test_imports():
    """Test if all modules can be imported."""
    modules = [
        "fastapi",
        "uvicorn", 
        "langchain",
        "openai",
        "google.cloud.videointelligence",
        "google.generativeai",
        "cv2"
    ]
    
    failed_imports = []
    for module in modules:
        try:
            __import__(module)
            logger.info(f"✅ {module} imported successfully")
        except ImportError as e:
            logger.error(f"❌ {module} import failed: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        logger.error(f"❌ Failed to import: {failed_imports}")
        return False
    
    return True

def main():
    """Main setup function."""
    logger.info("🚀 Starting Surveillance AI Local Setup...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create directories
    create_directories()
    
    # Check environment files
    env_ok = check_environment_files()
    
    # Test imports
    imports_ok = test_imports()
    
    if env_ok and imports_ok:
        logger.info("\n🎉 Setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Fill in your API keys in .env file")
        logger.info("2. Add your Google Cloud credentials.json")
        logger.info("3. Run: python main.py")
        return True
    else:
        logger.error("\n❌ Setup incomplete. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 