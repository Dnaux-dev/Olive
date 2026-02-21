import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api"

def test_full_auth_flow():
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    phone = f"+234{uuid.uuid4().hex[:8]}"
    password = "SecurePassword123"
    
    print(f"--- Testing with Email: {email} ---")
    
    # 1. Register
    reg_payload = {
        "phone_number": phone,
        "email": email,
        "name": "Test User",
        "password": password
    }
    
    print(f"1. Attempting Registration...")
    reg_res = requests.post(f"{BASE_URL}/users/", json=reg_payload)
    print(f"Registration Status: {reg_res.status_code}")
    print(f"Registration Body: {reg_res.text}")
    
    if reg_res.status_code != 200:
        print("❌ Registration failed.")
        return

    # 2. Login
    login_payload = {
        "email": email,
        "password": password
    }
    
    print(f"\n2. Attempting Login...")
    login_res = requests.post(f"{BASE_URL}/users/login", json=login_payload)
    print(f"Login Status: {login_res.status_code}")
    print(f"Login Body: {login_res.text}")
    
    if login_res.status_code == 200:
        print("✅ Login successful!")
    else:
        print("❌ Login failed.")

    # 3. Test existing error
    print(f"\n3. Attempting Duplicate Registration...")
    dup_res = requests.post(f"{BASE_URL}/users/", json=reg_payload)
    print(f"Duplicate Reg Status: {dup_res.status_code}")
    print(f"Duplicate Reg Body: {dup_res.text}")

if __name__ == "__main__":
    test_full_auth_flow()
