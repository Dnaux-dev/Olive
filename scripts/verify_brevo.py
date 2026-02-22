
import sys
import os
import logging

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.email_service import get_email_service
from config import get_settings

logging.basicConfig(level=logging.INFO)

def test_brevo_integration():
    print("Verifying Brevo Integration...")
    settings = get_settings()
    
    if not settings.brevo_api_key:
        print("⚠️ Brevo API key not found in settings. Please update your .env file.")
        return
        
    print(f"Brevo Sender: {settings.brevo_from_email}")
    
    email_service = get_email_service()
    
    # Try sending a test OTP
    to_email = input("Enter an email to send a test OTP to: ")
    success = email_service.send_otp(to_email, "111222", "Brevo Tester")
    
    if success:
        print("✅ Brevo test email sent successfully!")
    else:
        print("❌ Brevo test email failed. Check logs for details.")

if __name__ == "__main__":
    test_brevo_integration()
