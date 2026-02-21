"""
Mock Doctor Service
Provides data for verified doctors on the platform
"""

from typing import List, Optional
import uuid

# Mock data for doctors
MOCK_DOCTORS = [
    {
        "id": "dr-001",
        "name": "Dr. Adebayo Ogunlesi",
        "specialty": "Obstetrician & Gynecologist",
        "category_id": "maternal_health",
        "experience_years": 12,
        "rating": 4.9,
        "review_count": 128,
        "availability": "Mon - Fri, 9:00 AM - 5:00 PM",
        "bio": "Expert in maternal health and high-risk pregnancies with over 12 years of clinical experience.",
        "profile_image_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Adebayo",
        "is_verified": True,
        "location": "Lagos, Nigeria",
        "consultation_fee": 15000.0
    },
    {
        "id": "dr-002",
        "name": "Dr. Chioma Okoro",
        "specialty": "Pediatrician",
        "category_id": "child_health",
        "experience_years": 8,
        "rating": 4.8,
        "review_count": 95,
        "availability": "Mon - Sat, 10:00 AM - 4:00 PM",
        "bio": "Passionate about infant care and childhood vaccinations. Specialized in neonatal health.",
        "profile_image_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Chioma",
        "is_verified": True,
        "location": "Abuja, Nigeria",
        "consultation_fee": 12000.0
    },
    {
        "id": "dr-003",
        "name": "Dr. Ibrahim Musa",
        "specialty": "Family Physician",
        "category_id": "general_practice",
        "experience_years": 15,
        "rating": 4.7,
        "review_count": 210,
        "availability": "Daily, 8:00 AM - 8:00 PM",
        "bio": "Comprehensive family medical care with a focus on preventative medicine and wellness.",
        "profile_image_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Ibrahim",
        "is_verified": True,
        "location": "Kano, Nigeria",
        "consultation_fee": 10000.0
    },
    {
        "id": "dr-004",
        "name": "Dr. Funke Akindele",
        "specialty": "Maternal-Fetal Medicine Specialist",
        "category_id": "maternal_health",
        "experience_years": 10,
        "rating": 4.9,
        "review_count": 84,
        "availability": "Tue, Thu, Sat, 9:00 AM - 3:00 PM",
        "bio": "Specialized in managing complex pregnancies and ensuring both mother and baby are healthy.",
        "profile_image_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Funke",
        "is_verified": True,
        "location": "Ibadan, Nigeria",
        "consultation_fee": 20000.0
    },
    {
        "id": "dr-005",
        "name": "Dr. Emeka Nwosu",
        "specialty": "Fertility Specialist",
        "category_id": "maternal_health",
        "experience_years": 18,
        "rating": 4.6,
        "review_count": 156,
        "availability": "Mon - Wed, 11:00 AM - 6:00 PM",
        "bio": "Helping couples achieve their dreams of parenthood through advanced fertility treatments.",
        "profile_image_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=Emeka",
        "is_verified": True,
        "location": "Enugu, Nigeria",
        "consultation_fee": 25000.0
    }
]

class DoctorService:
    def get_all_doctors(self) -> List[dict]:
        """Return all mock doctors"""
        return MOCK_DOCTORS

    def get_doctor_by_id(self, doctor_id: str) -> Optional[dict]:
        """Find a doctor by ID"""
        for doctor in MOCK_DOCTORS:
            if doctor["id"] == doctor_id:
                return doctor
        return None

    def search_doctors(self, specialty: Optional[str] = None, category_id: Optional[str] = None) -> List[dict]:
        """Search doctors by specialty or category"""
        results = MOCK_DOCTORS
        if specialty:
            results = [d for d in results if specialty.lower() in d["specialty"].lower()]
        if category_id:
            results = [d for d in results if d["category_id"] == category_id]
        return results

_doctor_service = None

def get_doctor_service():
    global _doctor_service
    if _doctor_service is None:
        _doctor_service = DoctorService()
    return _doctor_service
