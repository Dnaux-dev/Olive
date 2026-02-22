"""
AI Service
Handles medical reasoning and multilingual advice using Google Gemini
"""

import google.generativeai as genai
from config import get_settings
from typing import Dict, Any, List, Optional
import logging
import json
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_ai_api_key
        self.enabled = False
        
        if self.api_key and self.api_key != "your_google_ai_key":
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro-latest')
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
        You are Olive-AI, a medical assistant for visually impaired users. 
        You are empathetic, professional, and clear.
        
        User input: "{user_text}"
        
        Rules:
        1. Respond ONLY in the user's language (Yoruba, Hausa, or Igbo) if detection or context suggests it.
        2. Provide helpful first-aid advice or explanation of medications.
        3. ALWAYS include a disclaimer: "I am an AI, not a doctor. Please consult a medical professional."
        4. Keep responses concise (max 3-4 sentences) as they will be read aloud.
        5. Tone: Caring and supportive.
        """

        try:
            response = await self.model.generate_content_async(system_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return "Inú mi bà jẹ́, n kò leè fèsì rẹ́ báyìí. Jọ̀wọ́ ṣayẹwo dọ́kítà rẹ." if user_language == "yoruba" else "I'm sorry, I'm having trouble processing that right now. Please consult a doctor."

    async def get_drug_info_from_image(self, image_path: str) -> Optional[Dict]:
        """
        Analyze image (tablet, bottle, or prescription) to extract drug details
        Returns: Dict with drug_name, dosage, frequency, duration
        """
        if not self.enabled:
            return None

        try:
            image_data = Path(image_path).read_bytes()
            contents = [
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                },
                "Analyze this medical image (medication tablet, bottle, or prescription). "
                "Extract the drug name, dosage, frequency, and duration if visible. "
                "Return ONLY a JSON object with these keys: drug_name, dosage, frequency, duration. "
                "If something is not found, use null."
            ]
            
            response = await self.model.generate_content_async(contents)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return None

    async def lookup_drug_details(self, drug_name: str) -> Optional[Dict]:
        """
        Lookup drug information using AI as a fallback for Emdex
        """
        if not self.enabled:
            return None

        prompt = f"""
        Provide information about the drug: {drug_name}.
        Return ONLY a JSON object with these keys: 
        - name (str)
        - generic_name (str)
        - price_naira (float, estimated average in Nigeria)
        - manufacturer (str, common one in Nigeria)
        - therapeutic_class (str)
        - warnings (list of str)
        - generics (list of objects with name, price_naira, manufacturer, savings)
        
        If information is unknown, use null or empty values.
        """

        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini drug lookup error: {e}")
            return None

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
