import sys
import os
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.getcwd())

from app.services.email_service import get_email_service
from config import get_settings

def troubleshoot_email():
    settings = get_settings()
    email_service = get_email_service()
    
    print("--- Configuration Check ---")
    print(f"Resend API Key present: {'Yes' if settings.resend_api_key else 'No'}")
    print(f"Resend From Email: {settings.resend_from_email}")
    print(f"Resend Enabled in Service: {email_service.resend_enabled}")
    
    test_email = "ajiloredaniel33@gmail.com" # Using one of the user's emails
    print(f"\n--- Attempting Test Email to {test_email} ---")
    
    success = email_service.send_otp(test_email, "123456", "Diagnostic Test")
    
    if success:
        print("\n✅ Service reported success!")
        print("Please check your inbox (and SPAM folder) for 'Verify your Medi-Sync AI account'.")
    else:
        print("\n❌ Service reported failure.")
        print("Check the logs above for specific error messages from Resend.")

if __name__ == "__main__":
    troubleshoot_email()
