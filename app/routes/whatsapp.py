"""
WhatsApp Integration Endpoints
"""

from fastapi import APIRouter, HTTPException, Request
from ..models import WhatsAppWebhookPayload, SuccessResponse
from ..services.whatsapp_service import get_whatsapp_service
from ..services.database_service import get_db_service
from ..services.ocr_service import get_ocr_service
from ..services.pill_service import get_pill_service

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

@router.get("/webhook")
def verify_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    """WhatsApp webhook verification"""
    whatsapp_service = get_whatsapp_service()
    
    if hub_mode == "subscribe" and whatsapp_service.verify_webhook_token(hub_verify_token):
        return int(hub_challenge)
    
    raise HTTPException(status_code=403, detail="Webhook verification failed")

@router.post("/webhook", response_model=SuccessResponse)
async def handle_webhook(payload: dict):
    """Handle incoming WhatsApp messages"""
    whatsapp_service = get_whatsapp_service()
    db_service = get_db_service()
    
    try:
        # Parse incoming message
        message_data = whatsapp_service.parse_webhook(payload)
        
        if not message_data:
            return SuccessResponse(success=True, message="No messages to process")
        
        from_phone = message_data.get('from')
        message_type = message_data.get('type')
        
        # Get or create user
        user = db_service.get_user_by_phone(from_phone)
        if not user:
            # Create new user
            user_id = db_service.create_user({
                'phone_number': from_phone,
                'name': f'User {from_phone[-4:]}'
            })
            user = db_service.get_user(user_id)
        
        # Handle different message types
        if message_type == 'text':
            response = await handle_text_message(
                from_phone,
                user['id'],
                message_data.get('text')
            )
        elif message_type == 'image':
            response = await handle_image_message(
                from_phone,
                user['id'],
                message_data.get('image_id')
            )
        else:
            response = "Message type not supported yet"
        
        # Send response
        if response:
            whatsapp_service.send_message(from_phone, response)
        
        return SuccessResponse(success=True, message="Message processed")
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return SuccessResponse(success=True, message="Webhook processed")

async def handle_text_message(phone_number: str, user_id: str, text: str) -> str:
    """Handle text messages from WhatsApp"""
    db_service = get_db_service()
    whatsapp_service = get_whatsapp_service()
    
    text = text.lower().strip()
    
    # Command handling
    if text.startswith('/help'):
        return """
        Available commands:
        /medications - View active medications
        /reminders - View pending reminders
        /stats - View medication compliance stats
        /help - Show this message
        """
    
    elif text.startswith('/medications'):
        medications = db_service.get_user_medications(user_id, status='active')
        if not medications:
            return "You have no active medications."
        
        response = "Your medications:\n"
        for med in medications[:5]:  # Limit to 5
            response += f"• {med['drug_name']} {med['dosage']}\n"
        return response
    
    elif text.startswith('/reminders'):
        pending = db_service.get_pending_reminders(limit=5)
        pending = [r for r in pending if r['user_id'] == user_id]
        
        if not pending:
            return "No pending reminders."
        
        response = "Pending reminders:\n"
        for reminder in pending:
            response += f"• {reminder['drug_name']} - {reminder['reminder_datetime']}\n"
        return response
    
    elif text.startswith('/stats'):
        from ..services.reminder_service import get_reminder_service
        reminder_service = get_reminder_service()
        stats = reminder_service.get_reminder_stats(user_id)
        
        return f"""
        Your medication stats:
        Total reminders: {stats['total']}
        Sent: {stats['sent']}
        Taken: {stats['taken']}
        Pending: {stats['pending']}
        """
    
    elif text == 'taken':
        # Mark last reminder as taken
        from ..services.reminder_service import get_reminder_service
        reminder_service = get_reminder_service()
        
        pending = reminder_service.get_pending_reminders(user_id, limit=1)
        if pending:
            reminder_service.mark_reminder_taken(pending[0]['id'])
            return f"✅ Marked {pending[0]['drug_name']} as taken!"
        
        return "No pending reminders to mark as taken."
    
    else:
        # Default response
        return "Hi! I'm Medi-Sync. Type /help for available commands."

async def handle_image_message(phone_number: str, user_id: str, image_id: str) -> str:
    """Handle image messages (prescription uploads)"""
    whatsapp_service = get_whatsapp_service()
    ocr_service = get_ocr_service()
    db_service = get_db_service()
    
    try:
        # Download image from WhatsApp
        image_data = whatsapp_service.download_media(image_id)
        
        if not image_data:
            return "Sorry, I couldn't download the image. Please try again."
        
        # Process as prescription
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_data)
            tmp_path = tmp.name
        
        try:
            # Extract text
            ocr_text, confidence = ocr_service.extract_text_from_image(tmp_path)
            
            # Parse drugs
            drugs = ocr_service.parse_prescription(ocr_text)
            
            if not drugs:
                return "I couldn't identify any medications in the image. Please make sure it's a clear prescription."
            
            # Create prescription
            prescription_id = db_service.create_prescription(
                user_id=user_id,
                image_url=image_id,
                ocr_text=ocr_text
            )
            
            db_service.update_prescription(prescription_id, {
                'ocr_confidence': confidence,
                'status': 'processed'
            })
            
            # Add drugs
            for drug in drugs:
                db_service.add_drug_to_prescription(prescription_id, drug.to_dict())
            
            response = f"✅ I found {len(drugs)} medication(s):\n"
            for drug in drugs[:5]:
                response += f"• {drug.name}"
                if drug.dosage:
                    response += f" {drug.dosage}"
                response += "\n"
            
            response += "\nDo you want to set up reminders for these medications?"
            
            return response
        
        finally:
            os.unlink(tmp_path)
    
    except Exception as e:
        print(f"Image processing error: {e}")
        return "Sorry, I couldn't process the image. Please try again."
