"""
Database Service Layer
Handles all SQLite database operations with connection pooling
"""

import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import get_settings
import os

class DatabaseService:
    """SQLite database operations"""
    
    def __init__(self):
        self.db_path = get_settings().database_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure database file exists and create if needed"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Create database if it doesn't exist
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.close()
    
    @contextmanager
    def get_db(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False) -> Any:
        """Execute a SELECT query and return results"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query, returns affected rows"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query, returns last row id"""
        with self.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    # User operations
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        return self.execute_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
            fetch_one=True
        )
    
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict]:
        """Get user by phone number"""
        return self.execute_query(
            "SELECT * FROM users WHERE phone_number = ?",
            (phone_number,),
            fetch_one=True
        )
    
    def create_user(self, user_data: Dict) -> str:
        """Create new user, returns user_id"""
        user_id = user_data.get('id') or str(datetime.now().timestamp())
        
        self.execute_insert(
            """INSERT INTO users 
               (id, phone_number, name, age, gender, language_preference, reminders_enabled)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, user_data['phone_number'], user_data.get('name'),
             user_data.get('age'), user_data.get('gender'),
             user_data.get('language_preference', 'english'),
             user_data.get('reminders_enabled', True))
        )
        return user_id
    
    def update_user(self, user_id: str, updates: Dict) -> bool:
        """Update user information"""
        allowed_fields = ['name', 'age', 'gender', 'language_preference', 
                         'cycles_enabled', 'last_cycle_date', 'reminders_enabled']
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys() if k in allowed_fields])
        values = [v for k, v in updates.items() if k in allowed_fields]
        values.append(user_id)
        
        if set_clause:
            self.execute_update(
                f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                tuple(values)
            )
            return True
        return False
    
    # Prescription operations
    def create_prescription(self, user_id: str, image_url: str = None, ocr_text: str = None) -> int:
        """Create new prescription, returns prescription_id"""
        return self.execute_insert(
            """INSERT INTO prescriptions (user_id, image_url, ocr_text)
               VALUES (?, ?, ?)""",
            (user_id, image_url, ocr_text)
        )
    
    def get_prescription(self, prescription_id: int) -> Optional[Dict]:
        """Get prescription by ID"""
        return self.execute_query(
            "SELECT * FROM prescriptions WHERE id = ?",
            (prescription_id,),
            fetch_one=True
        )
    
    def get_user_prescriptions(self, user_id: str) -> List[Dict]:
        """Get all prescriptions for a user"""
        return self.execute_query(
            "SELECT * FROM prescriptions WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
    
    def update_prescription(self, prescription_id: int, updates: Dict) -> bool:
        """Update prescription"""
        allowed_fields = ['ocr_text', 'ocr_confidence', 'status', 'verified_by_user']
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys() if k in allowed_fields])
        values = [v for k, v in updates.items() if k in allowed_fields]
        values.append(prescription_id)
        
        if set_clause:
            self.execute_update(
                f"UPDATE prescriptions SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                tuple(values)
            )
            return True
        return False
    
    # Prescription drugs operations
    def add_drug_to_prescription(self, prescription_id: int, drug_data: Dict) -> int:
        """Add drug to prescription"""
        return self.execute_insert(
            """INSERT INTO prescription_drugs 
               (prescription_id, drug_name, dosage, frequency, duration, emdex_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (prescription_id, drug_data['drug_name'], drug_data.get('dosage'),
             drug_data.get('frequency'), drug_data.get('duration'),
             drug_data.get('emdex_id'))
        )
    
    def get_prescription_drugs(self, prescription_id: int) -> List[Dict]:
        """Get all drugs for a prescription"""
        return self.execute_query(
            "SELECT * FROM prescription_drugs WHERE prescription_id = ?",
            (prescription_id,)
        )
    
    # Medication operations
    def create_medication(self, medication_data: Dict) -> int:
        """Create new medication, returns medication_id"""
        return self.execute_insert(
            """INSERT INTO medications 
               (user_id, prescription_id, drug_name, emdex_id, dosage, frequency, 
                start_date, end_date, reminder_times, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (medication_data['user_id'], medication_data.get('prescription_id'),
             medication_data['drug_name'], medication_data.get('emdex_id'),
             medication_data.get('dosage'), medication_data.get('frequency'),
             medication_data['start_date'], medication_data.get('end_date'),
             medication_data.get('reminder_times'), medication_data.get('status', 'active'))
        )
    
    def get_medication(self, medication_id: int) -> Optional[Dict]:
        """Get medication by ID"""
        return self.execute_query(
            "SELECT * FROM medications WHERE id = ?",
            (medication_id,),
            fetch_one=True
        )
    
    def get_user_medications(self, user_id: str, status: str = 'active') -> List[Dict]:
        """Get user's active medications"""
        if status == 'all':
            return self.execute_query(
                "SELECT * FROM medications WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
        return self.execute_query(
            "SELECT * FROM medications WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
            (user_id, status)
        )
    
    def update_medication(self, medication_id: int, updates: Dict) -> bool:
        """Update medication"""
        allowed_fields = ['dosage', 'frequency', 'end_date', 'reminder_times', 'status', 'side_effects']
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys() if k in allowed_fields])
        values = [v for k, v in updates.items() if k in allowed_fields]
        values.append(medication_id)
        
        if set_clause:
            self.execute_update(
                f"UPDATE medications SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                tuple(values)
            )
            return True
        return False
    
    # Reminder operations
    def create_reminder(self, reminder_data: Dict) -> int:
        """Create new reminder, returns reminder_id"""
        return self.execute_insert(
            """INSERT INTO reminders 
               (user_id, medication_id, reminder_datetime, delivery_status)
               VALUES (?, ?, ?, ?)""",
            (reminder_data['user_id'], reminder_data['medication_id'],
             reminder_data['reminder_datetime'], reminder_data.get('delivery_status', 'pending'))
        )
    
    def get_pending_reminders(self, limit: int = 100) -> List[Dict]:
        """Get reminders that haven't been sent yet"""
        return self.execute_query(
            """SELECT r.*, m.drug_name, m.dosage, u.phone_number, u.language_preference
               FROM reminders r
               JOIN medications m ON r.medication_id = m.id
               JOIN users u ON r.user_id = u.id
               WHERE r.delivery_status = 'pending' AND r.reminder_datetime <= datetime('now')
               ORDER BY r.reminder_datetime ASC
               LIMIT ?""",
            (limit,)
        )
    
    def update_reminder(self, reminder_id: int, updates: Dict) -> bool:
        """Update reminder status"""
        allowed_fields = ['sent', 'sent_at', 'delivery_status', 'whatsapp_message_id']
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys() if k in allowed_fields])
        values = [v for k, v in updates.items() if k in allowed_fields]
        values.append(reminder_id)
        
        if set_clause:
            self.execute_update(
                f"UPDATE reminders SET {set_clause} WHERE id = ?",
                tuple(values)
            )
            return True
        return False
    
    # Drug database operations
    def create_drug(self, drug_data: Dict) -> int:
        """Create new drug in database"""
        return self.execute_insert(
            """INSERT INTO drug_database 
               (emdex_id, name, generic_name, therapeutic_class, price_naira, 
                manufacturer, generics, warnings, nafdac_verified)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (drug_data['emdex_id'], drug_data['name'], drug_data.get('generic_name'),
             drug_data.get('therapeutic_class'), drug_data.get('price_naira'),
             drug_data.get('manufacturer'), drug_data.get('generics'),
             drug_data.get('warnings'), drug_data.get('nafdac_verified', False))
        )
    
    def get_drug(self, emdex_id: str) -> Optional[Dict]:
        """Get drug by emdex_id"""
        return self.execute_query(
            "SELECT * FROM drug_database WHERE emdex_id = ?",
            (emdex_id,),
            fetch_one=True
        )
    
    def search_drugs(self, query: str) -> List[Dict]:
        """Search drugs by name"""
        return self.execute_query(
            """SELECT * FROM drug_database 
               WHERE name LIKE ? OR generic_name LIKE ? 
               LIMIT 10""",
            (f"%{query}%", f"%{query}%")
        )
    
    # Audit logging
    def log_action(self, user_id: str, action: str, entity_type: str = None,
                  entity_id: str = None, details: Dict = None, ip_address: str = None) -> int:
        """Log user action for audit trail"""
        import json
        details_json = json.dumps(details) if details else None
        
        return self.execute_insert(
            """INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, action, entity_type, entity_id, details_json, ip_address)
        )

# Singleton instance
_db_service = None

def get_db_service() -> DatabaseService:
    """Get or create database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
