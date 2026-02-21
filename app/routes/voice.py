"""
Voice Consultation API Endpoints
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from fastapi.responses import FileResponse
from typing import Optional
import os
import uuid
from ..services.ai_service import get_ai_service
from ..services.voice_service import get_voice_service
from ..services.database_service import get_db_service

router = APIRouter(prefix="/api/voice", tags=["voice"])

@router.post("/consult")
async def voice_consult(
    user_id: str,
    file: UploadFile = File(...),
    language: str = "english"
):
    """
    Handle voice-based medical consultation
    Flow: STT -> AI Analysis -> TTS (YarnGPT)
    """
    ai_service = get_ai_service()
    voice_service = get_voice_service()
    db_service = get_db_service()
    
    # 1. Verify user
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 2. Save uploaded audio temporarily
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    input_path = os.path.join(temp_dir, f"input_{file_id}_{file.filename}")
    
    try:
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # 3. Speech to Text (STT)
        user_text = voice_service.speech_to_text(input_path)
        
        # 4. Get AI Advice (Gemini)
        ai_response_text = await ai_service.get_medical_advice(user_text, language)
        
        # 5. Text to Speech (YarnGPT)
        output_filename = f"response_{file_id}.mp3"
        output_path = os.path.join(temp_dir, output_filename)
        voice_service.text_to_speech_yarngpt(ai_response_text, language, output_path)
        
        # 6. Response
        return {
            "user_text": user_text,
            "ai_response": ai_response_text,
            "audio_url": f"/api/voice/audio/{output_filename}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup input file
        if os.path.exists(input_path):
            os.remove(input_path)

@router.get("/audio/{filename}")
async def get_audio_response(filename: str):
    """Serve the generated audio response"""
    file_path = os.path.join("temp_audio", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")
