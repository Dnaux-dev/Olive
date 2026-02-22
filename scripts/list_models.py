
import google.generativeai as genai
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from config import get_settings

def list_models():
    settings = get_settings()
    genai.configure(api_key=settings.google_ai_api_key)
    print("Listing available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model: {m.name}")

if __name__ == "__main__":
    list_models()
