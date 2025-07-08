from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pyngrok import ngrok
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Surveillance AI Backend",
    description="AI-powered surveillance system backend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://preview--surveillanceai.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create required directories
def create_required_directories():
    directories = [
        "content/uploads",
        "content/logs"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# Import and include routers
from routes import router as api_router
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    # Create required directories
    create_required_directories()
    
    # Start ngrok
    try:
        public_url = ngrok.connect(8000)
        logger.info(f"Ngrok tunnel established at: {public_url}")
    except Exception as e:
        logger.error(f"Failed to start ngrok: {str(e)}")
    
    # Start FastAPI server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 