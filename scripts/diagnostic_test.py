
import sys
import os
import asyncio
import logging

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.services.ocr_service import get_ocr_service
from app.services.voice_service import get_voice_service
from app.services.ai_service import get_ai_service
from config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_diagnostics():
    print("=== Medi-Sync AI Diagnostics ===")
    settings = get_settings()
    
    # 1. OCR Diagnostics
    print("\n--- OCR Service ---")
    ocr_service = get_ocr_service()
    print(f"Using Mock OCR: {ocr_service.use_mock}")
    print(f"Credentials Path: {ocr_service.google_credentials_path}")
    print(f"File exists: {os.path.exists(ocr_service.google_credentials_path)}")
    
    test_image = "/Users/mac/.gemini/antigravity/brain/84a0206f-cf86-4882-afb0-2f51423cbade/test_paracetamol_prescription_1771728851844.png"
    if os.path.exists(test_image):
        print(f"Testing OCR with generated image: {test_image}")
        text, confidence = ocr_service.extract_text_from_image(test_image)
        print(f"Extracted Text (first 100 chars): {text[:100]}...")
        print(f"Confidence: {confidence}")
        
        drugs = ocr_service.parse_prescription(text)
        print(f"Parsed Drugs: {[d.to_dict() for d in drugs]}")
    else:
        print(f"❌ Test image not found at {test_image}")

    # 2. Voice Diagnostics
    print("\n--- Voice Service ---")
    voice_service = get_voice_service()
    test_audio_path = "scripts/test_audio.wav" # Placeholder
    stt_result = voice_service.speech_to_text(test_audio_path)
    print(f"STT Result (Mock): {stt_result}")
    
    # 3. AI Service (Gemini)
    print("\n--- AI Service ---")
    ai_service = get_ai_service()
    print(f"Gemini Enabled: {ai_service.enabled}")
    if ai_service.enabled:
        advice = await ai_service.get_medical_advice("I have a headache. Orí mń fọ́ mi.", "yoruba")
        print(f"AI Response (Yoruba): {advice}")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
