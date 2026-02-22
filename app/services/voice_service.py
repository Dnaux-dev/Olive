"""
Voice Service
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) via YarnGPT
"""

import requests
import os
import logging
from config import get_settings
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        settings = get_settings()
        self.yarngpt_key = settings.yarngpt_api_key
        self.yarngpt_url = "https://yarngpt.ai/api/v1/generate" # Placeholder for actual endpoint
        
    def speech_to_text(self, audio_file_path: str) -> str:
        """
        Convert audio file to text
        TODO: Integrate with Google Speech-to-Text or OpenAI Whisper
        """
        logger.info(f"STT: Processing {audio_file_path}")
        # Placeholder/Mock: In a real scenario, we'd send this to a STT API
        return "I have a sharp pain in my stomach and I need help."

    def text_to_speech_yarngpt(self, text: str, language: str = "yoruba", output_path: str = "response.mp3") -> Optional[str]:
        """
        Convert text to authentic Nigerian speech using YarnGPT
        """
        if not self.yarngpt_key:
            logger.warning("YARNGPT_API_KEY not set. Using mock TTS.")
            return self._mock_tts(text, output_path)

        headers = {
            "Authorization": f"Bearer {self.yarngpt_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "language": language,
            "voice": "standard_yoruba" # Depends on YarnGPT's voice options
        }

        try:
            response = requests.post(self.yarngpt_url, json=payload, headers=headers)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
            else:
                logger.error(f"YarnGPT TTS failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error calling YarnGPT: {e}")
            return None

    def _mock_tts(self, text: str, output_path: str) -> str:
        """Mock TTS for development"""
        logger.info(f"MOCK TTS: Generating audio for: {text}")
        # Create an empty file to simulate audio generation
        with open(output_path, "w") as f:
            f.write("MOCK AUDIO CONTENT")
        return output_path

# Singleton instance
_voice_service = None

def get_voice_service() -> VoiceService:
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
