import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"
USER_ID = "1c59e995-5c54-418b-9d95-5a39ebd35bb6" # Using the user created earlier

def test_create_medication():
    url = f"{BASE_URL}/medications/{USER_ID}"
    
    # Payload matching MedicationCreate model
    payload = {
        "drug_name": "Paracetamol",
        "dosage": "500mg",
        "frequency": "Three times daily",
        "start_date": datetime.now().isoformat(),
        "reminder_times": ["08:00", "14:00", "20:00"]
    }
    
    print(f"Testing create medication: {url}")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
    
    if response.status_code == 200:
        return response.json().get('id')
    return None

def test_schedule_reminders(med_id):
    if not med_id:
        print("Skipping schedule reminders test (no med_id)")
        return
        
    url = f"{BASE_URL}/reminders/{med_id}"
    # This expects List[str]
    payload = ["09:00", "15:00", "21:00"]
    
    print(f"\nTesting schedule reminders: {url}")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

def test_drug_search():
    url = f"{BASE_URL}/drugs/search"
    print(f"\nTesting drug search: {url}")
    response = requests.get(url, params={"query": "Paracetamol"})
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

if __name__ == "__main__":
    med_id = test_create_medication()
    test_schedule_reminders(med_id)
    test_drug_search()
