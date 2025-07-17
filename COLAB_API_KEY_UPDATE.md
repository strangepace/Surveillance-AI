# 🔧 Colab API Key Update Instructions

After rotating your API keys, you need to update them in your Google Colab notebook. Here's how:

## Option 1: Update .env file (Recommended)

1. **Upload new .env file to Google Drive:**
   - Create a new `.env` file with your rotated keys:
   ```
   OPENAI_API_KEY=sk-your-new-openai-key
   GEMINI_API_KEY=your-new-gemini-key
   ```
   - Upload this file to your Google Drive `surveillance-ai` folder

2. **Reload the .env file in Colab:**
   - Add this cell to your Colab notebook after the environment variables cell:
   ```python
   # Reload .env file with new keys
   from dotenv import load_dotenv
   load_dotenv(env_path, override=True)
   
   # Verify keys are loaded
   openai_key = os.getenv('OPENAI_API_KEY')
   gemini_key = os.getenv('GEMINI_API_KEY')
   
   print(f"🔑 OpenAI API Key loaded: {'✅' if openai_key else '❌'}")
   print(f"🔑 Gemini API Key loaded: {'✅' if gemini_key else '❌'}")
   ```

## Option 2: Set Environment Variables Directly

Add this cell to your Colab notebook:

```python
# Set new API keys directly
import os

# Replace with your new API keys
os.environ['OPENAI_API_KEY'] = 'sk-your-new-openai-key'
os.environ['GEMINI_API_KEY'] = 'your-new-gemini-key'

# Verify keys are set
openai_key = os.getenv('OPENAI_API_KEY')
gemini_key = os.getenv('GEMINI_API_KEY')

print(f"🔑 OpenAI API Key loaded: {'✅' if openai_key else '❌'}")
print(f"🔑 Gemini API Key loaded: {'✅' if gemini_key else '❌'}")

if openai_key and gemini_key:
    print("✅ API keys are ready for use!")
else:
    print("❌ Please check your API keys.")
```

## ✅ Verification

After updating the keys, run a test to verify everything works:

```python
# Test API functionality
test_video_analysis('content/uploads/your_video.mp4', 'Detect any objects')
```

## 🔒 Security Note

- Never commit API keys to Git
- Always use environment variables or .env files
- Rotate keys regularly for security
- The local backend automatically loads keys from .env
- Only Colab needs manual key updates since it doesn't auto-load .env 