import requests
import json

BASE_URL = "http://localhost:8000/api"

def debug_registration():
    payload = {
        "phone_number": "09013093765",
        "email": "ajiloredaniel33@gmail.com",
        "name": "Daniel",
        "password": "password123"
    }
    
    print(f"Attempting to register: {payload['email']} / {payload['phone_number']}")
    try:
        response = requests.post(f"{BASE_URL}/users/", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_registration()
