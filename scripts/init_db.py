"""
SQLite Database Initialization Script
Creates all tables and indexes for Medi-Sync AI application
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

def init_database(db_path: str = "./data/medi_sync.db"):
    """Initialize SQLite database with schema"""
    
    # Create data directory if it doesn't exist
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    print("Creating tables...")
    
    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            phone_number TEXT UNIQUE NOT NULL,
            email TEXT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            language_preference TEXT DEFAULT 'english',
            cycles_enabled BOOLEAN DEFAULT 0,
            last_cycle_date TIMESTAMP,
            reminders_enabled BOOLEAN DEFAULT 1,
            email_reminders_enabled BOOLEAN DEFAULT 1,
            email_verified BOOLEAN DEFAULT 0,
            password_hash TEXT,
            whatsapp_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Prescriptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            image_url TEXT,
            ocr_text TEXT,
            ocr_confidence REAL,
            status TEXT DEFAULT 'pending',
            verified_by_user BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # 3. Prescription drugs junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescription_drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id INTEGER NOT NULL,
            drug_name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            duration TEXT,
            emdex_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
        )
    """)
    
    # 4. Medications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            prescription_id INTEGER,
            drug_name TEXT NOT NULL,
            emdex_id TEXT,
            dosage TEXT,
            frequency TEXT,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP,
            reminder_times TEXT,
            reminders_sent INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            side_effects TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(prescription_id) REFERENCES prescriptions(id) ON DELETE SET NULL
        )
    """)
    
    # 5. Pills table (for pill verification)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name TEXT UNIQUE NOT NULL,
            shape TEXT,
            color TEXT,
            imprint TEXT,
            ml_model_id TEXT,
            image_url TEXT,
            emdex_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 6. Drug database (Emdex cache)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emdex_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            generic_name TEXT,
            therapeutic_class TEXT,
            price_naira REAL,
            manufacturer TEXT,
            generics TEXT,
            warnings TEXT,
            nafdac_verified BOOLEAN,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 7. Reminders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            medication_id INTEGER NOT NULL,
            reminder_datetime TIMESTAMP NOT NULL,
            sent BOOLEAN DEFAULT 0,
            sent_at TIMESTAMP,
            delivery_status TEXT DEFAULT 'pending',
            whatsapp_message_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(medication_id) REFERENCES medications(id) ON DELETE CASCADE
        )
    """)
    
    # 8. Audit logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
        )
    """)
    
    # 9. Registered drugs table (Safe List)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registered_drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_number TEXT NOT NULL UNIQUE,
            product_name TEXT NOT NULL,
            manufacturer TEXT,
            category TEXT,
            is_verified BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed common drugs
    print("Seeding registered drugs...")
    common_drugs = [
        ("A4-0102", "Panadol Advance", "GlaxoSmithKline", "Analgesic"),
        ("04-2345", "Amoxil Capsules", "GSK Nigeria", "Antibiotic"),
        ("04-5678", "Emzor Paracetamol", "Emzor Pharmaceuticals", "Analgesic"),
        ("A4-9876", "Lonart DS", "Greenlife Pharmaceuticals", "Antimalarial"),
        ("04-1122", "Coartem 80/480", "Novartis", "Antimalarial"),
        ("B4-5566", "Ventolin Inhaler", "Glaxo Wellcome", "Respiratory"),
        ("04-7788", "Augmentin 625mg", "Beecham", "Antibiotic")
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO registered_drugs (reg_number, product_name, manufacturer, category)
        VALUES (?, ?, ?, ?)
    """, common_drugs)
    
    # Create indexes for better query performance
    print("Creating indexes...")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prescriptions_user ON prescriptions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prescriptions_status ON prescriptions(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_medications_user ON medications(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_medications_status ON medications(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_datetime ON reminders(reminder_datetime)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(delivery_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drug_database_emdex ON drug_database(emdex_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_drug_database_name ON drug_database(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pills_drug_name ON pills(drug_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_registered_drugs_reg ON registered_drugs(reg_number)")
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {db_path}")

if __name__ == "__main__":
    db_path = os.getenv("DATABASE_PATH", "./data/medi_sync.db")
    init_database(db_path)
