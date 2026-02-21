import sqlite3
import firebase_admin
from firebase_admin import credentials, db
import os
import sys

# Add the project root to sys.path to import config
sys.path.append(os.getcwd())
from config import get_settings

def clear_all_data():
    print("🚀 Starting full data wipe...")
    settings = get_settings()
    
    # 1. Clear SQLite Database
    db_path = settings.database_path
    if os.path.exists(db_path):
        print(f"--- Clearing SQLite database at {db_path} ---")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Disable foreign key checks temporarily to avoid constraint issues during bulk delete
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # List of tables to clear (in order to avoid most issues)
            tables = [
                "audit_logs",
                "reminders",
                "medications",
                "prescription_drugs",
                "prescriptions",
                "users"
            ]
            
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
                print(f"✅ Cleared table: {table}")
            
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.commit()
            conn.close()
            print("✨ SQLite data wiped successfully.")
        except Exception as e:
            print(f"❌ Error clearing SQLite: {e}")
    else:
        print("⚠️ SQLite database file not found.")

    # 2. Clear Firebase Realtime Database
    print("\n--- Clearing Firebase Realtime Database ---")
    creds_path = settings.firebase_service_account_key_path
    if os.path.exists(creds_path):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': settings.firebase_database_url
                })
            
            # Delete the 'users' and 'sync_logs' nodes
            db.reference('users').delete()
            print("✅ Cleared 'users' node in Firebase")
            db.reference('sync_logs').delete()
            print("✅ Cleared 'sync_logs' node in Firebase")
            print("✨ Firebase data wiped successfully.")
        except Exception as e:
            print(f"❌ Error clearing Firebase: {e}")
    else:
        print("⚠️ Firebase credentials not found, skipping Firebase wipe.")

    print("\n🏁 Full data wipe completed.")

if __name__ == "__main__":
    clear_all_data()
