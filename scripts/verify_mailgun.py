
import sys
import os
import logging

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.email_service import get_email_service
from config import get_settings

logging.basicConfig(level=logging.INFO)

def test_mailgun_integration():
    print("Verifying Mailgun Integration...")
    settings = get_settings()
    
    if not settings.mailgun_api_key or not settings.mailgun_domain:
        print("⚠️ Mailgun credentials not found in settings. Please update your .env file.")
        return
        
    print(f"Mailgun Domain: {settings.mailgun_domain}")
    print(f"Mailgun Endpoint: {settings.mailgun_endpoint}")
    
    email_service = get_email_service()
    
    # Try sending a test OTP
    to_email = input("Enter an email to send a test OTP to: ")
    success = email_service.send_otp(to_email, "999888", "Mailgun Tester")
    
    if success:
        print("✅ Mailgun test email sent successfully!")
    else:
        print("❌ Mailgun test email failed. Check logs for details.")

if __name__ == "__main__":
    test_mailgun_integration()
