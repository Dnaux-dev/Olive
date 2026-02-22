"""
Reminder Service
Handles medication reminder scheduling and delivery
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from .database_service import get_db_service
from .firebase_service import get_firebase_service
from .whatsapp_service import get_whatsapp_service

class ReminderService:
    """Medication reminder management"""
    
    def __init__(self):
        self.db_service = get_db_service()
        self.firebase_service = get_firebase_service()
        self.whatsapp_service = get_whatsapp_service()
        from .email_service import get_email_service
        self.email_service = get_email_service()
    
    def schedule_reminder(self, medication_id: int, reminder_times: List[str]) -> List[int]:
        """
        Schedule reminders for a medication
        reminder_times: List of times in HH:MM format
        Returns: List of reminder IDs created
        """
        # Get medication details
        medication = self.db_service.get_medication(medication_id)
        if not medication:
            return []
        
        reminder_ids = []
        start_date = datetime.fromisoformat(medication['start_date'])
        end_date = medication['end_date']
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        else:
            # Default to 30 days if no end date
            end_date = start_date + timedelta(days=30)
        
        current_date = start_date
        
        # Create reminders for each day in medication duration
        while current_date <= end_date:
            for time_str in reminder_times:
                try:
                    hours, minutes = map(int, time_str.split(':'))
                    reminder_datetime = current_date.replace(hour=hours, minute=minutes)
                    
                    # Skip if reminder is in the past
                    if reminder_datetime < datetime.now():
                        continue
                    
                    reminder_id = self.db_service.create_reminder({
                        'user_id': medication['user_id'],
                        'medication_id': medication_id,
                        'reminder_datetime': reminder_datetime.isoformat(),
                        'delivery_status': 'pending'
                    })
                    
                    reminder_ids.append(reminder_id)
                except ValueError:
                    continue
            
            current_date += timedelta(days=1)
        
        return reminder_ids
    
    def get_pending_reminders(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get reminders that are due to be sent"""
        if user_id:
            return self.db_service.execute_query(
                """SELECT r.*, m.drug_name, m.dosage, u.phone_number, u.language_preference
                   FROM reminders r
                   JOIN medications m ON r.medication_id = m.id
                   JOIN users u ON r.user_id = u.id
                   WHERE r.user_id = ? AND r.delivery_status = 'pending' 
                   AND r.reminder_datetime <= datetime('now')
                   ORDER BY r.reminder_datetime ASC
                   LIMIT ?""",
                (user_id, limit)
            )
        else:
            return self.db_service.get_pending_reminders(limit)
    
    async def send_reminder(self, reminder_id: int) -> Dict:
        """Send a reminder via WhatsApp and Email (Async)"""
        reminder = self.db_service.execute_query(
            """SELECT r.*, m.drug_name, m.dosage, u.phone_number, u.email, 
                      u.name as user_name, u.language_preference, u.email_reminders_enabled
               FROM reminders r
               JOIN medications m ON r.medication_id = m.id
               JOIN users u ON r.user_id = u.id
               WHERE r.id = ?""",
            (reminder_id,),
            fetch_one=True
        )
        
        if not reminder:
            return {'success': False, 'error': 'Reminder not found'}
        
        results = {'whatsapp': False, 'email': False, 'sms': False}
        errors = []

        # 1. Send via WhatsApp
        medication = {
            'drug_name': reminder['drug_name'],
            'dosage': reminder['dosage']
        }
        
        if reminder['phone_number']:
            wa_result = await self.whatsapp_service.send_reminder(
                reminder['phone_number'],
                medication,
                reminder.get('language_preference', 'english')
            )
            results['whatsapp'] = wa_result.get('success', False)
            if not results['whatsapp']:
                errors.append(f"WhatsApp: {wa_result.get('error')}")

        # 2. Send via Email
        if reminder['email'] and reminder.get('email_reminders_enabled'):
            email_result = await self.email_service.send_reminder(
                reminder['email'],
                medication,
                reminder.get('user_name', 'User')
            )
            results['email'] = email_result
            if not email_result:
                errors.append("Email delivery failed")
        
        # 3. Send via SMS
        if reminder['phone_number']:
            sms_message = f"🔔 Olive-AI Reminder: Time to take your {reminder['drug_name']} {reminder['dosage']}."
            # Simple localization for SMS
            if reminder.get('language_preference') == 'yoruba':
                sms_message = f"🔔 Olive-AI: Akoko lati mu {reminder['drug_name']} {reminder['dosage']} re ti to."
            elif reminder.get('language_preference') == 'hausa':
                sms_message = f"🔔 Olive-AI: Lokacin shan maganin {reminder['drug_name']} {reminder['dosage']} ya yi."
            elif reminder.get('language_preference') == 'igbo':
                sms_message = f"🔔 Olive-AI: Oge erugo iji {reminder['drug_name']} {reminder['dosage']} gị."

            sms_result = await self.email_service.send_sms(reminder['phone_number'], sms_message)
            results['sms'] = sms_result
            if not sms_result:
                errors.append("SMS delivery failed")
        
        # Update reminder status (Succeed if at least one channel worked)
        if results['whatsapp'] or results['email'] or results['sms']:
            self.db_service.update_reminder(reminder_id, {
                'sent': True,
                'sent_at': datetime.now().isoformat(),
                'delivery_status': 'sent'
            })
            
            # Push to Firebase for real-time delivery
            self.firebase_service.push_reminder(
                reminder['user_id'],
                reminder_id,
                {
                    'medication_id': reminder['medication_id'],
                    'drug_name': reminder['drug_name'],
                    'dosage': reminder['dosage'],
                    'reminder_datetime': reminder['reminder_datetime']
                }
            )
            
            return {'success': True, 'channels': results}
        else:
            self.db_service.update_reminder(reminder_id, {
                'delivery_status': 'failed'
            })
            return {'success': False, 'error': "; ".join(errors)}
    
    async def send_all_due_reminders(self) -> Dict:
        """Send all reminders that are due (Async)"""
        pending = self.get_pending_reminders()
        
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for reminder in pending:
            result = await self.send_reminder(reminder['id'])
            if result['success']:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'reminder_id': reminder['id'],
                    'error': result.get('error')
                })
        
        return results
    
    def snooze_reminder(self, reminder_id: int, minutes: int = 5) -> bool:
        """Snooze a reminder for specified minutes"""
        reminder = self.db_service.execute_query(
            "SELECT reminder_datetime FROM reminders WHERE id = ?",
            (reminder_id,),
            fetch_one=True
        )
        
        if not reminder:
            return False
        
        current_time = datetime.fromisoformat(reminder['reminder_datetime'])
        new_time = current_time + timedelta(minutes=minutes)
        
        return self.db_service.execute_update(
            """UPDATE reminders SET reminder_datetime = ?, delivery_status = 'pending'
               WHERE id = ?""",
            (new_time.isoformat(), reminder_id)
        ) > 0
    
    def mark_reminder_taken(self, reminder_id: int) -> bool:
        """Mark reminder as taken by user"""
        return self.db_service.update_reminder(reminder_id, {
            'delivery_status': 'taken',
            'sent_at': datetime.now().isoformat()
        })
    
    def get_user_reminders(self, user_id: str, 
                          status: str = 'pending', 
                          days: int = 7) -> List[Dict]:
        """Get user's reminders for specified period"""
        end_date = datetime.now() + timedelta(days=days)
        
        if status == 'all':
            return self.db_service.execute_query(
                """SELECT r.*, m.drug_name, m.dosage
                   FROM reminders r
                   JOIN medications m ON r.medication_id = m.id
                   WHERE r.user_id = ? AND r.reminder_datetime <= ?
                   ORDER BY r.reminder_datetime ASC""",
                (user_id, end_date.isoformat())
            )
        
        return self.db_service.execute_query(
            """SELECT r.*, m.drug_name, m.dosage
               FROM reminders r
               JOIN medications m ON r.medication_id = m.id
               WHERE r.user_id = ? AND r.delivery_status = ? AND r.reminder_datetime <= ?
               ORDER BY r.reminder_datetime ASC""",
            (user_id, status, end_date.isoformat())
        )
    
    def get_reminder_stats(self, user_id: str) -> Dict:
        """Get reminder statistics for user"""
        total = self.db_service.execute_query(
            "SELECT COUNT(*) as count FROM reminders WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        sent = self.db_service.execute_query(
            "SELECT COUNT(*) as count FROM reminders WHERE user_id = ? AND delivery_status = 'sent'",
            (user_id,),
            fetch_one=True
        )
        
        taken = self.db_service.execute_query(
            "SELECT COUNT(*) as count FROM reminders WHERE user_id = ? AND delivery_status = 'taken'",
            (user_id,),
            fetch_one=True
        )
        
        return {
            'total': total['count'] if total else 0,
            'sent': sent['count'] if sent else 0,
            'taken': taken['count'] if taken else 0,
            'pending': (total['count'] if total else 0) - (sent['count'] if sent else 0)
        }

# Singleton instance
_reminder_service = None

def get_reminder_service() -> ReminderService:
    """Get or create reminder service instance"""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
    return _reminder_service
