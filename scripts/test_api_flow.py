import requests
import json
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

def test_api_flow():
    print("--- Starting API Flow Test ---")
    
    # 1. Create User
    phone = f"+234{uuid.uuid4().hex[:8]}"
    print(f"1. Creating user with phone: {phone}")
    user_payload = {
        "phone_number": phone,
        "name": "Test User",
        "age": 30,
        "gender": "male",
        "language_preference": "english"
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=user_payload)
    if response.status_code != 200:
        print(f"FAILED: Create User ({response.status_code}): {response.text}")
        return
    
    user = response.json()
    user_id = user['id']
    print(f"SUCCESS: User created with ID: {user_id}")
    
    # 2. Get User
    print("2. Verifying user lookup...")
    response = requests.get(f"{BASE_URL}/users/{user_id}")
    if response.status_code == 200:
        print("SUCCESS: User found")
    else:
        print(f"FAILED: User lookup ({response.status_code})")
        
    # 3. Create Medication
    print("3. Creating medication for user")
    start_date = datetime.now().isoformat()
    med_payload = {
        "drug_name": "Paracetamol",
        "dosage": "500mg",
        "frequency": "twice daily",
        "start_date": start_date,
        "reminder_times": ["08:00", "20:00"]
    }
    
    response = requests.post(f"{BASE_URL}/medications/{user_id}", json=med_payload)
    if response.status_code != 200:
        print(f"FAILED: Create Medication ({response.status_code}): {response.text}")
        return
    
    medication = response.json()
    med_id = medication['id']
    print(f"SUCCESS: Medication created with ID: {med_id}")
    
    # 4. Get Reminders
    print("4. Checking for scheduled reminders")
    response = requests.get(f"{BASE_URL}/reminders/user/{user_id}")
    if response.status_code == 200:
        reminders = response.json()
        print(f"SUCCESS: Found {len(reminders)} reminders")
    else:
        print(f"FAILED: Fetch reminders ({response.status_code})")

    # 5. Search Drugs
    print("5. Searching drug database for 'Amoxicillin'")
    response = requests.get(f"{BASE_URL}/drugs/search?query=Amoxicillin")
    if response.status_code == 200:
        results = response.json().get('results', [])
        print(f"SUCCESS: Found {len(results)} matches in database")
    else:
        print(f"FAILED: Drug search ({response.status_code})")

    print("\n--- API Flow Test Completed ---")

if __name__ == "__main__":
    test_api_flow()
