"""
Email Service Layer
Handles sending OTPs and medication reminders via SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config import get_settings
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self.settings = get_settings()
        self.enabled = bool(self.settings.smtp_username and self.settings.smtp_password)
        if not self.enabled:
            logger.warning("Email service disabled: SMTP credentials not provided")
    
    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Core method to send email"""
        if not self.enabled:
            logger.info(f"MOCK EMAIL to {to_email}: {subject}")
            logger.debug(f"Body: {html_body}")
            return True # Return true for mock/dev
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.settings.smtp_from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port) as server:
                server.starttls()
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                server.send_message(msg)
                
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_otp(self, to_email: str, otp_code: str, user_name: str = "User") -> bool:
        """Send OTP verification code"""
        subject = "Verify your Medi-Sync AI account"
        body = f"""
        <html>
            <body>
                <h2>Hello {user_name},</h2>
                <p>Your verification code for Medi-Sync AI is:</p>
                <h1 style="color: #4A90E2; letter-spacing: 5px;">{otp_code}</h1>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        return self._send_email(to_email, subject, body)

    def send_reminder(self, to_email: str, medication: Dict, user_name: str = "User") -> bool:
        """Send medication reminder"""
        drug_name = medication.get('drug_name', 'your medication')
        dosage = medication.get('dosage', '')
        
        subject = f"Reminder: Time to take your {drug_name}"
        body = f"""
        <html>
            <body>
                <h2>Hi {user_name},</h2>
                <p>This is a reminder from Medi-Sync AI to take your medication.</p>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 5px solid #28a745;">
                    <strong>{drug_name}</strong><br>
                    Dosage: {dosage}
                </div>
                <p>Please log in to the app to mark it as taken.</p>
                <br>
                <small>Stay healthy!</small>
            </body>
        </html>
        """
        return self._send_email(to_email, subject, body)

# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
