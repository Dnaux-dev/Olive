
import sys
import os
import logging

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.email_service import get_email_service
from config import get_settings

logging.basicConfig(level=logging.INFO)

def test_email_sending():
    print("Testing Email Service...")
    settings = get_settings()
    print(f"SMTP Server: {settings.smtp_server}")
    print(f"SMTP Port: {settings.smtp_port}")
    print(f"SMTP Username: {settings.smtp_username}")
    print(f"SMTP From: {settings.smtp_from_email}")
    
    email_service = get_email_service()
    
    # Try sending to the same email as username for testing
    to_email = settings.smtp_username
    success = email_service.send_otp(to_email, "123456", "Test Admin")
    
    if success:
        print("✅ Email sent successfully!")
    else:
        print("❌ Email sending failed. Check logs for details.")

if __name__ == "__main__":
    test_email_sending()
