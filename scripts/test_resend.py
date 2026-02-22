
import requests
import os

def test_resend():
    api_key = "re_AfQHCZsc_DGtQZuyutB9UP7PW7N972E4m"
    from_email = "onboarding@resend.dev"
    to_email = "danielajilore12@gmail.com" # A common email from the user's data
    
    print(f"Testing Resend API with Key: {api_key[:10]}...")
    
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": from_email,
            "to": to_email,
            "subject": "Resend Test from Olive",
            "html": "<strong>It works!</strong>",
        },
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_resend()
