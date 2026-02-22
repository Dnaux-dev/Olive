import requests
import os

def test_prescription_upload():
    # Use a real user ID or a mock one if the system allows
    # In my experience, 'test_user' might not exist, but let's check
    user_id = "1c59e995-5c54-418b-9d95-5a39ebd35bb6"
    url = f"http://localhost:8000/api/prescriptions/{user_id}/upload"
    
    # Path to a dummy image
    image_path = "test_drug.jpg"
    # Create a dummy image if it doesn't exist
    if not os.path.exists(image_path):
        with open(image_path, "wb") as f:
            f.write(b"dummy image content")
    
    print(f"Testing upload to {url}...")
    
    try:
        # Correct way to send file + form data
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/jpeg")}
            data = {"auto_match": "true"}
            
            response = requests.post(url, files=files, data=data)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
    except Exception as e:
        print(f"Error during request: {e}")
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

if __name__ == "__main__":
    test_prescription_upload()
