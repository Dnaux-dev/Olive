"""
Firebase Service Layer
Handles Firebase Realtime Database operations for real-time sync and reminders
"""

import firebase_admin
from firebase_admin import db, credentials
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from config import get_settings

class FirebaseService:
    """Firebase Realtime Database operations"""
    
    def __init__(self):
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase if not already done"""
        try:
            app = firebase_admin.get_app()
            self.initialized = True
        except ValueError:
            # Firebase not initialized yet
            settings = get_settings()
            creds_path = settings.firebase_service_account_key_path
            
            if not os.path.exists(creds_path):
                print(f"Warning: Firebase credentials not found at {creds_path}")
                self.initialized = False
                return
            
            try:
                cred = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': settings.firebase_database_url
                })
                self.initialized = True
            except Exception as e:
                print(f"Failed to initialize Firebase: {e}")
                self.initialized = False
    
    def _is_available(self) -> bool:
        """Check if Firebase is available"""
        return self.initialized
    
    # User profile operations
    def sync_user_profile(self, user_id: str, user_data: Dict) -> bool:
        """Sync user profile to Firebase"""
        if not self._is_available():
            return False
        
        try:
            ref = db.reference(f'users/{user_id}/profile')
            # Prepare data for Firebase (remove internal fields)
            firebase_data = {
                'phone_number': user_data.get('phone_number'),
                'name': user_data.get('name'),
                'language_preference': user_data.get('language_preference'),
                'reminders_enabled': user_data.get('reminders_enabled'),
                'last_updated': datetime.now().isoformat()
            }
            ref.set(firebase_data)
            return True
        except Exception as e:
            print(f"Error syncing user profile: {e}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile from Firebase"""
        if not self._is_available():
            return None
        
        try:
            ref = db.reference(f'users/{user_id}/profile')
            data = ref.get()
            return data.val() if data else None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    # Medication operations
    def sync_user_medications(self, user_id: str, medications: List[Dict]) -> bool:
        """Sync user's medications to Firebase"""
        if not self._is_available():
            return False
        
        try:
            ref = db.reference(f'users/{user_id}/medications')
            firebase_medications = {}
            
            for med in medications:
                med_id = str(med['id'])
                firebase_medications[med_id] = {
                    'drug_name': med.get('drug_name'),
                    'dosage': med.get('dosage'),
                    'frequency': med.get('frequency'),
                    'start_date': med.get('start_date'),
                    'end_date': med.get('end_date'),
                    'status': med.get('status'),
                    'reminder_times': med.get('reminder_times')
                }
            
            ref.set(firebase_medications)
            return True
        except Exception as e:
            print(f"Error syncing medications: {e}")
            return False
    
    def get_user_medications(self, user_id: str) -> Optional[Dict]:
        """Get user's medications from Firebase"""
        if not self._is_available():
            return None
        
        try:
            ref = db.reference(f'users/{user_id}/medications')
            data = ref.get()
            return data.val() if data else {}
        except Exception as e:
            print(f"Error getting medications: {e}")
            return None
    
    # Reminder operations
    def push_reminder(self, user_id: str, reminder_id: int, reminder_data: Dict) -> bool:
        """Push reminder to Firebase for real-time delivery"""
        if not self._is_available():
            return False
        
        try:
            ref = db.reference(f'users/{user_id}/reminders/{reminder_id}')
            firebase_reminder = {
                'medication_id': reminder_data.get('medication_id'),
                'drug_name': reminder_data.get('drug_name'),
                'dosage': reminder_data.get('dosage'),
                'reminder_datetime': reminder_data.get('reminder_datetime'),
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
            ref.set(firebase_reminder)
            return True
        except Exception as e:
            print(f"Error pushing reminder: {e}")
            return False
    
    def update_reminder_status(self, user_id: str, reminder_id: int, status: str) -> bool:
        """Update reminder status in Firebase"""
        if not self._is_available():
            return False
        
        try:
            ref = db.reference(f'users/{user_id}/reminders/{reminder_id}')
            ref.update({
                'status': status,
                'updated_at': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            print(f"Error updating reminder status: {e}")
            return False
    
    def get_user_pending_reminders(self, user_id: str) -> Optional[Dict]:
        """Get pending reminders for user"""
        if not self._is_available():
            return None
        
        try:
            ref = db.reference(f'users/{user_id}/reminders')
            data = ref.get()
            if not data:
                return {}
            
            reminders = data.val()
            # Filter for pending reminders
            pending = {k: v for k, v in reminders.items() 
                      if v.get('status') == 'pending'}
            return pending
        except Exception as e:
            print(f"Error getting pending reminders: {e}")
            return None
    
    # Sync tracking
    def update_last_sync(self, user_id: str) -> bool:
        """Update user's last sync timestamp"""
        if not self._is_available():
            return False
        
        try:
            ref = db.reference(f'users/{user_id}/lastSync')
            ref.set(datetime.now().isoformat())
            return True
        except Exception as e:
            print(f"Error updating last sync: {e}")
            return False
    
    def log_sync(self, user_id: str, action: str, details: Dict = None) -> bool:
        """Log sync action for debugging"""
        if not self._is_available():
            return False
        
        try:
            sync_id = datetime.now().timestamp()
            ref = db.reference(f'sync_logs/{user_id}/{sync_id}')
            log_data = {
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'details': details or {}
            }
            ref.set(log_data)
            return True
        except Exception as e:
            print(f"Error logging sync: {e}")
            return False
    
    # Listener setup (for real-time updates)
    def listen_user_reminders(self, user_id: str, callback) -> bool:
        """Set up listener for user's reminders"""
        if not self._is_available():
            return False
        
        try:
            ref = db.reference(f'users/{user_id}/reminders')
            ref.listen(callback)
            return True
        except Exception as e:
            print(f"Error setting up reminder listener: {e}")
            return False
    
    # Bulk operations
    def create_user_structure(self, user_id: str) -> bool:
        """Create initial user structure in Firebase"""
        if not self._is_available():
            return False
        
        try:
            ref = db.reference(f'users/{user_id}')
            initial_data = {
                'profile': {},
                'medications': {},
                'reminders': {},
                'lastSync': None
            }
            ref.set(initial_data)
            return True
        except Exception as e:
            print(f"Error creating user structure: {e}")
            return False
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data from Firebase"""
        if not self._is_available():
            return False
        
        try:
            ref = db.reference(f'users/{user_id}')
            ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting user data: {e}")
            return False

# Singleton instance
_firebase_service = None

def get_firebase_service() -> FirebaseService:
    """Get or create Firebase service instance"""
    global _firebase_service
    if _firebase_service is None:
        _firebase_service = FirebaseService()
    return _firebase_service
