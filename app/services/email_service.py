"""
Email & SMS Service Layer
Handles sending OTPs and medication reminders via Brevo, Resend, or SMTP
"""

import logging
import httpx
from config import get_settings
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via Resend API or SMTP fallback"""
    
    def __init__(self):
        self.settings = get_settings()
        self.brevo_enabled = bool(self.settings.brevo_api_key)
        self.resend_enabled = bool(self.settings.resend_api_key)
        self.smtp_enabled = bool(self.settings.smtp_username and self.settings.smtp_password)
        self.sms_enabled = bool(self.settings.brevo_api_key)
        
        if not self.brevo_enabled and not self.resend_enabled and not self.smtp_enabled:
            logger.warning("Email service disabled: No Brevo, Resend, or SMTP credentials provided")
    
    async def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Core method to send email using prioritized providers (Async)"""
        if self.brevo_enabled:
            return await self._send_via_brevo(to_email, subject, html_body)
        elif self.resend_enabled:
            return await self._send_via_resend(to_email, subject, html_body)
        elif self.smtp_enabled:
            return await self._send_via_smtp(to_email, subject, html_body)
            
        logger.info(f"MOCK EMAIL to {to_email}: {subject}")
        return True

    async def _send_via_brevo(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via Brevo API (Async)"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.brevo.com/v3/smtp/email",
                    headers={
                        "api-key": self.settings.brevo_api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "sender": {"email": self.settings.brevo_from_email, "name": "Olive-AI"},
                        "to": [{"email": to_email}],
                        "subject": subject,
                        "htmlContent": html_body
                    }
                )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent via Brevo to {to_email}")
                return True
            else:
                logger.error(f"Brevo API error: {response.status_code} - {response.text}")
                # Fallback to other providers if Brevo fails
                if self.resend_enabled:
                    return await self._send_via_resend(to_email, subject, html_body)
                elif self.smtp_enabled:
                    return await self._send_via_smtp(to_email, subject, html_body)
                return False
        except Exception as e:
            logger.error(f"Failed to send email via Brevo: {e}")
            return False

    async def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS via Brevo API (Async)"""
        if not self.sms_enabled:
            logger.warning(f"SMS disabled. MOCK SMS to {to_phone}: {message}")
            return True
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.brevo.com/v3/transactionalSMS/sms",
                    headers={
                        "api-key": self.settings.brevo_api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "type": "transactional",
                        "sender": "OliveAI",
                        "recipient": to_phone,
                        "content": message
                    }
                )
            
            if response.status_code in [200, 201]:
                logger.info(f"SMS sent via Brevo to {to_phone}")
                return True
            else:
                logger.error(f"Brevo SMS API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send SMS via Brevo: {e}")
            return False

    async def _send_via_resend(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via Resend API (Async)"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self.settings.resend_from_email,
                        "to": to_email,
                        "subject": subject,
                        "html": html_body,
                    }
                )
            
            if response.status_code in [200, 201]:
                logger.info(f"Email sent via Resend to {to_email}")
                return True
            else:
                logger.error(f"Resend API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send email via Resend: {e}")
            return False

    async def _send_via_smtp(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via legacy SMTP (Async Wrapper)"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
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
            logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
            return False

    async def send_otp(self, to_email: str, otp_code: str, user_name: str = "User") -> bool:
        """Send OTP verification code (Async)"""
        subject = "Verify your Olive-AI account"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #4A90E2;">Hello {user_name},</h2>
                    <p>Welcome to Olive-AI. Please use the verification code below to complete your registration:</p>
                    <div style="background-color: #f4f7f6; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                        <h1 style="color: #4A90E2; letter-spacing: 5px; margin: 0; font-size: 40px;">{otp_code}</h1>
                    </div>
                    <p>This code will expire in 10 minutes. If you did not request this, please ignore this email.</p>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #999; text-align: center;">© 2024 Olive-AI. All rights reserved.</p>
                </div>
            </body>
        </html>
        """
        return self._send_email(to_email, subject, body)

    async def send_reminder(self, to_email: str, medication: Dict, user_name: str = "User") -> bool:
        """Send medication reminder (Async)"""
        drug_name = medication.get('drug_name', 'your medication')
        dosage = medication.get('dosage', '')
        
        subject = f"Reminder: Time to take your {drug_name}"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #28a745;">Time for your Medication</h2>
                    <p>Hi {user_name}, this is a reminder to take your medication as scheduled:</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 5px solid #28a745; margin: 20px 0;">
                        <strong style="font-size: 18px;">{drug_name}</strong><br>
                        <span style="color: #666;">Dosage: {dosage}</span>
                    </div>
                    <p>Please log in to the app to mark it as taken so we can track your progress.</p>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <small style="color: #999;">Stay healthy! – The Olive-AI Team</small>
                </div>
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
