"""
AI Service
Handles medical reasoning and multilingual advice using Google Gemini
"""

import google.generativeai as genai
from config import get_settings
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_ai_api_key
        self.enabled = False
        
        if self.api_key and self.api_key != "your_google_ai_key":
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.enabled = True
                logger.info("Gemini AI Service initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")
        else:
            logger.warning("GOOGLE_AI_API_KEY not found. AI features will run in MOCK mode.")

    async def get_medical_advice(self, user_text: str, user_language: str = "english") -> str:
        """
        Get medical guidance based on symptoms or queries
        """
        if not self.enabled:
            return self._mock_response(user_text, user_language)

        system_prompt = f"""
        You are Medi-Sync AI, a medical assistant for visually impaired users. 
        You are empathetic, professional, and clear.
        
        User input: "{user_text}"
        
        Rules:
        1. If the input is in Yoruba or contextually implies a Yoruba user, respond ONLY in Yoruba.
        2. Provide helpful first-aid advice or explanation of medications.
        3. ALWAYS include a disclaimer: "I am an AI, not a doctor. Please consult a medical professional."
        4. Keep responses concise (max 3-4 sentences) as they will be read aloud.
        5. Tone: Caring and supportive.
        """

        try:
            response = self.model.generate_content(system_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return "Inú mi bà jẹ́, n kò leè fèsì rẹ́ báyìí. Jọ̀wọ́ ṣayẹwo dọ́kítà rẹ." if user_language == "yoruba" else "I'm sorry, I'm having trouble processing that right now. Please consult a doctor."

    def _mock_response(self, text: str, lang: str) -> str:
        """Fallback response when AI is disabled"""
        if "headache" in text.lower() or "orí" in text.lower():
            return "Pẹ̀lẹ́. O le lo Paracetamol fún orí fífọ̀ náà. Ṣùgbọ́n jọ̀wọ́ rí dọ́kítà rẹ. (I'm an AI assistant)." if lang == "yoruba" else "I understand you have a headache. You might consider rest and Paracetamol, but please consult a doctor. (AI Mock)"
        
        return "N kò mọ̀ báyìí, jọ̀wọ́ ṣàlàyé sí i. (Please explain more. I am an AI assistant.)" if lang == "yoruba" else "I'm here to help, but I need more details. Please consult a doctor. (AI Mock)"

# Singleton instance
_ai_service = None

def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
