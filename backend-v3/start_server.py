#!/usr/bin/env python3
"""
Script to start the FastAPI server and test it
"""
import subprocess
import time
import requests
import sys
import os

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    print("📍 Directory:", os.getcwd())
    print("📁 Files:", [f for f in os.listdir('.') if f.endswith('.py')])
    
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'app:app', 
            '--host', '127.0.0.1', '--port', '8002'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Test the server
        try:
            response = requests.get('http://127.0.0.1:8002/health', timeout=5)
            print(f"✅ Server is running!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            
            # Keep server running
            print("🔄 Server is running. Press Ctrl+C to stop.")
            process.wait()
            
        except requests.exceptions.ConnectionError:
            print("❌ Server failed to start")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    start_server() 