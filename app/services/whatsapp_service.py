"""
WhatsApp Service
Handles WhatsApp Cloud API integration for reminders and notifications
"""

import httpx
import json
import hmac
import hashlib
from typing import Dict, Optional, Any
from config import get_settings
import logging

logger = logging.getLogger(__name__)

class WhatsAppMessage:
    """WhatsApp message structure"""
    def __init__(self, message_type: str, recipient_phone: str, content: Dict):
        self.message_type = message_type  # 'text', 'template', 'interactive'
        self.recipient_phone = recipient_phone
        self.content = content

class WhatsAppService:
    """WhatsApp Cloud API operations"""
    
    def __init__(self):
        settings = get_settings()
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        self.webhook_token = settings.whatsapp_webhook_token
        self.business_account_id = settings.whatsapp_business_account_id
        self.api_url = "https://graph.instagram.com/v18.0"
        self.use_mock = not (self.phone_number_id and self.access_token)
    
    def verify_webhook_token(self, token: str) -> bool:
        """Verify webhook token for WhatsApp"""
        return token == self.webhook_token
    
    def parse_webhook(self, payload: Dict) -> Optional[Dict]:
        """Parse incoming WhatsApp webhook payload"""
        try:
            entry = payload.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return None
            
            message = messages[0]
            return {
                'from': message.get('from'),
                'type': message.get('type'),
                'timestamp': message.get('timestamp'),
                'text': message.get('text', {}).get('body') if message.get('text') else None,
                'image': message.get('image', {}).get('id') if message.get('image') else None,
                'message_id': message.get('id')
            }
        except Exception as e:
            logger.error(f"Error parsing webhook: {e}")
            return None
    
    async def send_message(self, phone_number: str, text: str, 
                    template_name: str = None, params: Dict = None) -> Dict:
        """Send WhatsApp message (Async)"""
        if self.use_mock:
            return await self._mock_send_message(phone_number, text)
        
        try:
            if template_name:
                return await self._send_template_message(phone_number, template_name, params)
            else:
                return await self._send_text_message(phone_number, text)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _send_text_message(self, phone_number: str, text: str) -> Dict:
        """Send plain text message (Async)"""
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone_number,
            'type': 'text',
            'text': {'body': text}
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f'{self.api_url}/{self.phone_number_id}/messages',
                json=payload,
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'message_id': data.get('messages', [{}])[0].get('id')
            }
        else:
            return {
                'success': False,
                'error': response.text
            }
    
    async def _send_template_message(self, phone_number: str, template_name: str, 
                               params: Dict = None) -> Dict:
        """Send template message (Async)"""
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone_number,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': 'en_US'}
            }
        }
        
        # Add parameters if provided
        if params:
            payload['template']['components'] = [
                {
                    'type': 'body',
                    'parameters': [{'type': 'text', 'text': str(v)} for v in params.values()]
                }
            ]
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f'{self.api_url}/{self.phone_number_id}/messages',
                json=payload,
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'message_id': data.get('messages', [{}])[0].get('id')
            }
        else:
            return {
                'success': False,
                'error': response.text
            }
    
    async def _mock_send_message(self, phone_number: str, text: str) -> Dict:
        """Mock message sending for development (Async)"""
        import uuid
        message_id = str(uuid.uuid4())
        logger.info(f"MOCK: Sending message to {phone_number}: {text}")
        return {
            'success': True,
            'message_id': message_id
        }
    
    async def send_reminder(self, phone_number: str, medication: Dict, 
                     language: str = 'english') -> Dict:
        """Send medication reminder (Async)"""
        # ... exists ...
        return await self.send_message(phone_number, message_text)
    
    async def send_generic_suggestion(self, phone_number: str, drug: Dict, 
                               language: str = 'english') -> Dict:
        """Send generic drug suggestion (Async)"""
        # ... exists ...
        return await self.send_message(phone_number, message_text)
    
    async def send_verification_request(self, phone_number: str) -> Dict:
        """Send WhatsApp verification code (Async)"""
        code = self._generate_verification_code()
        message = f"Your Medi-Sync verification code is: {code}"
        
        result = await self.send_message(phone_number, message)
        if result.get('success'):
            result['code'] = code
        
        return result
    
    def _generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Download media from WhatsApp (Async)"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get media URL
                response = await client.get(
                    f'{self.api_url}/{media_id}',
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    media_url = data.get('url')
                    
                    # Download media
                    media_response = await client.get(
                        media_url,
                        headers=headers
                    )
                    
                    if media_response.status_code == 200:
                        return media_response.content
        
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
        
        return None
    
    async def mark_message_read(self, message_id: str) -> Dict:
        """Mark message as read (Async)"""
        if self.use_mock:
            return {'success': True}
        
        try:
            payload = {
                'messaging_product': 'whatsapp',
                'status': 'read',
                'message_id': message_id
            }
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f'{self.api_url}/{self.phone_number_id}/messages',
                    json=payload,
                    headers=headers
                )
            
            return {
                'success': response.status_code == 200,
                'error': response.text if response.status_code != 200 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Singleton instance
_whatsapp_service = None

def get_whatsapp_service() -> WhatsAppService:
    """Get or create WhatsApp service instance"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
