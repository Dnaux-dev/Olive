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
    
    def send_reminder(self, reminder_id: int) -> Dict:
        """Send a reminder via WhatsApp"""
        reminder = self.db_service.execute_query(
            """SELECT r.*, m.drug_name, m.dosage, u.phone_number, u.language_preference
               FROM reminders r
               JOIN medications m ON r.medication_id = m.id
               JOIN users u ON r.user_id = u.id
               WHERE r.id = ?""",
            (reminder_id,),
            fetch_one=True
        )
        
        if not reminder:
            return {'success': False, 'error': 'Reminder not found'}
        
        # Send via WhatsApp
        medication = {
            'drug_name': reminder['drug_name'],
            'dosage': reminder['dosage']
        }
        
        result = self.whatsapp_service.send_reminder(
            reminder['phone_number'],
            medication,
            reminder.get('language_preference', 'english')
        )
        
        # Update reminder status
        if result.get('success'):
            self.db_service.update_reminder(reminder_id, {
                'sent': True,
                'sent_at': datetime.now().isoformat(),
                'delivery_status': 'sent',
                'whatsapp_message_id': result.get('message_id')
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
            
            self.firebase_service.update_reminder_status(
                reminder['user_id'],
                reminder_id,
                'sent'
            )
            
            return {'success': True, 'message_id': result.get('message_id')}
        else:
            self.db_service.update_reminder(reminder_id, {
                'delivery_status': 'failed'
            })
            return {'success': False, 'error': result.get('error')}
    
    def send_all_due_reminders(self) -> Dict:
        """Send all reminders that are due"""
        pending = self.get_pending_reminders()
        
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for reminder in pending:
            result = self.send_reminder(reminder['id'])
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
