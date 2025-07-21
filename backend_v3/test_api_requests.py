import requests

files = {'file': open('content/uploads/naani.mp4', 'rb')}
data = {'prompts': 'elderly man, red shirt, car'}

response = requests.post("http://localhost:8000/analyze", files=files, data=data)

print("Status:", response.status_code)
try:
    print("Response:", response.json())
except Exception as e:
    print("Failed to parse JSON response:", e)
    print("Raw response:", response.text) 