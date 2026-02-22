import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.ocr_service import get_ocr_service
from app.services.drug_service import get_drug_service
from app.services.email_service import get_email_service
from app.services.ai_service import get_ai_service

async def test_enhancements():
    # 1. Test AI Drug Lookup
    print("\n--- Testing AI Drug Lookup Fallback ---")
    drug_service = get_drug_service()
    drug_name = "Artemether/Lumefantrine"
    print(f"Looking up: {drug_name}")
    match = await drug_service.match_drug_emdex(drug_name)
    if match:
        print(f"Found: {match.name}")
        print(f"Generic: {match.generic_name}")
        print(f"Est. Price: ₦{match.price_naira}")
        print(f"Generics found: {len(match.generics)}")
    else:
        print("Drug not found (AI fallback failed or disabled)")

    # 2. Test SMS Delivery (Mock/Brevo)
    print("\n--- Testing SMS Delivery ---")
    comm_service = get_email_service()
    phone = "+2348000000000"
    message = "🔔 Olive-AI Test: This is a sample reminder."
    success = comm_service.send_sms(phone, message)
    print(f"SMS Sent to {phone}: {success}")

    # 3. Test AI Image Analysis (Prescription/Tablet)
    # Since we don't have a real tablet image easy to path, 
    # we'll test the service method if AI is enabled
    ai_service = get_ai_service()
    if ai_service.enabled:
        print("\n--- Testing AI System Prompt (Multilingual) ---")
        yoruba_resp = await ai_service.get_medical_advice("I have stomach pain", "yoruba")
        print(f"Yoruba Response: {yoruba_resp[:100]}...")
    else:
        print("\nAI Service is in MOCK mode. Skipping live AI tests.")

if __name__ == "__main__":
    asyncio.run(test_enhancements())
