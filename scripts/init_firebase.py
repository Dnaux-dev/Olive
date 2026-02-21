"""
Firebase Realtime Database Initialization Script
Sets up initial Firebase Realtime DB structure for real-time sync and reminders
"""

import firebase_admin
from firebase_admin import db, credentials
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def init_firebase(credentials_path: str = None):
    """Initialize Firebase Realtime Database structure"""
    
    if credentials_path is None:
        credentials_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH", "./firebase-credentials.json")
    
    if not Path(credentials_path).exists():
        print(f"Firebase credentials file not found at {credentials_path}")
        print("Please download your Firebase service account key from Firebase Console")
        print("and save it to the specified path.")
        return False
    
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
    except ValueError:
        # Default app doesn't exist, so initialize it
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv('FIREBASE_DATABASE_URL', 'https://your-project.firebaseio.com')
        })
    
    print("Setting up Firebase Realtime Database structure...")
    
    # Initialize root structure
    ref = db.reference('/')
    
    # Create initial structure
    initial_data = {
        'users': {},
        'reminders': {},
        'medications': {},
        'sync_logs': {}
    }
    
    ref.set(initial_data)
    
    print("Firebase Realtime Database structure initialized")
    print("\nStructure created:")
    print("- /users/{userId}/profile")
    print("- /users/{userId}/medications")
    print("- /users/{userId}/lastSync")
    print("- /reminders/{userId}/{reminderId}")
    print("- /medications/{medicationId}")
    print("- /sync_logs (tracking database syncs)")
    
    return True

def create_user_structure(user_id: str):
    """Create user-specific structure in Firebase"""
    
    ref = db.reference(f'users/{user_id}')
    
    user_data = {
        'profile': {},
        'medications': {},
        'reminders': {},
        'lastSync': None
    }
    
    ref.set(user_data)
    print(f"User structure created for {user_id}")

def create_reminder_listener(user_id: str, callback):
    """Set up listener for user's reminders"""
    
    ref = db.reference(f'users/{user_id}/reminders')
    ref.listen(callback)
    print(f"Reminder listener attached for {user_id}")

if __name__ == "__main__":
    init_firebase()
