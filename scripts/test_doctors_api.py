from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_get_doctors():
    response = client.get("/api/doctors")
    assert response.status_code == 200
    data = response.json()
    assert "doctors" in data
    assert "total_count" in data
    assert len(data["doctors"]) == 5
    print("✅ test_get_doctors passed")

def test_get_doctor_details():
    response = client.get("/api/doctors/dr-001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "dr-001"
    assert data["name"] == "Dr. Adebayo Ogunlesi"
    print("✅ test_get_doctor_details passed")

def test_get_doctor_categories():
    response = client.get("/api/doctors/categories")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "categories" in data["data"]
    print("✅ test_get_doctor_categories passed")

def test_search_doctors():
    # Test specialty filter
    response = client.get("/api/doctors?specialty=Pediatrician")
    assert response.status_code == 200
    data = response.json()
    assert len(data["doctors"]) == 1
    assert data["doctors"][0]["specialty"] == "Pediatrician"
    
    # Test category filter
    response = client.get("/api/doctors?category_id=maternal_health")
    assert response.status_code == 200
    data = response.json()
    assert len(data["doctors"]) == 3
    print("✅ test_search_doctors passed")

if __name__ == "__main__":
    try:
        test_get_doctors()
        test_get_doctor_details()
        test_get_doctor_categories()
        test_search_doctors()
        print("\n✨ All backend doctor API tests passed!")
    except Exception as e:
        print(f"❌ Tests failed: {e}")
