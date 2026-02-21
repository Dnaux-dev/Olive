"""
Verification Service
Handles drug authenticity checks and NAFDAC number validation
"""

import re
from typing import Dict, Any, List, Optional
from .database_service import get_db_service

class VerificationService:
    def __init__(self):
        self.db_service = get_db_service()
        # Common NAFDAC formats: A4-XXXX, 04-XXXX, B4-XXXX
        self.nafdac_pattern = re.compile(r'^[A-Z0-9]{2}-[0-9]{4,6}$', re.IGNORECASE)

    def verify_drug(self, reg_number: str) -> Dict[str, Any]:
        """
        Verify a drug by its NAFDAC registration number
        """
        reg_number = reg_number.strip().upper()
        
        # 1. Validate Format
        if not self.nafdac_pattern.match(reg_number):
            return {
                "status": "invalid_format",
                "message": f"'{reg_number}' does not match the standard NAFDAC registration format (e.g., A4-1234).",
                "verification_tips": [
                    "Check the packaging for a number starting with A4, 04, B4, or NR.",
                    "Ensure the number is clearly printed and has not been tampered with.",
                    "Look for the NAFDAC logo near the registration number."
                ]
            }

        # 2. Check Local Safe List
        drug = self.db_service.execute_query(
            "SELECT * FROM registered_drugs WHERE reg_number = ?",
            (reg_number,),
            fetch_one=True
        )

        if drug:
            return {
                "status": "verified",
                "message": "This product is found in our database of NAFDAC-registered medicines.",
                "product_details": {
                    "name": drug['product_name'],
                    "manufacturer": drug['manufacturer'],
                    "category": drug['category'],
                    "reg_number": drug['reg_number']
                },
                "verification_tips": [
                    "Verify that the manufacturer name on the pack matches GSK, Emzor, etc.",
                    "Check the expiry date on the pack.",
                    "If a scratch panel is present, SMS the code to 38353 for final confirmation."
                ]
            }

        # 3. Suspicious / Not Found
        return {
            "status": "suspicious",
            "message": "WARNING: This registration number was not found in our verified database.",
            "verification_tips": [
                "This could be a new registration or a potential counterfeit.",
                "Check for a scratch panel and SMS the hidden code to 38353 (Standard NAFDAC verification).",
                "Look for the NAFDAC holographic seal on the packaging.",
                "Report suspicious drugs to the nearest NAFDAC office or via their mobile app."
            ]
        }

# Singleton instance
_verification_service = None

def get_verification_service() -> VerificationService:
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service
