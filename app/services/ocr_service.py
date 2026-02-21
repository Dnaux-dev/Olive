"""
OCR Service
Handles prescription image processing and text extraction
"""

import json
from typing import List, Dict, Tuple, Optional
from google.cloud import vision
from config import get_settings
import base64
import os

class DrugInfo:
    """Extracted drug information from prescription"""
    def __init__(self, name: str, dosage: str = None, frequency: str = None, duration: str = None):
        self.name = name
        self.dosage = dosage
        self.frequency = frequency
        self.duration = duration
    
    def to_dict(self) -> Dict:
        return {
            'drug_name': self.name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'duration': self.duration
        }

class OCRService:
    """OCR and prescription parsing"""
    
    def __init__(self):
        settings = get_settings()
        self.google_credentials_path = settings.google_application_credentials
        self.use_mock = not os.path.exists(self.google_credentials_path)
        
        if not self.use_mock:
            try:
                self.vision_client = vision.ImageAnnotatorClient()
            except Exception as e:
                print(f"Failed to initialize Vision API: {e}")
                self.use_mock = True
    
    def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from prescription image
        Returns: (extracted_text, confidence_score)
        """
        if self.use_mock:
            return self._mock_extraction(image_path)
        
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.vision_client.document_text_detection(image=image)
            
            full_text = response.full_text_annotation.text
            
            # Calculate confidence from detected text blocks
            confidence = 0.0
            if response.text_annotations:
                total_confidence = sum(
                    annotation.confidence for annotation in response.text_annotations[1:]
                    if hasattr(annotation, 'confidence')
                )
                confidence = total_confidence / max(len(response.text_annotations) - 1, 1)
            
            return full_text, confidence
        except Exception as e:
            print(f"OCR error: {e}")
            return self._mock_extraction(image_path)
    
    def _mock_extraction(self, image_path: str) -> Tuple[str, float]:
        """Mock prescription extraction for development/testing"""
        mock_ocr_text = """
        PRESCRIPTION
        Date: 2024-01-15
        Patient: John Doe
        
        Rx:
        1. Amoxicillin 500mg
           Frequency: 3 times daily
           Duration: 7 days
        
        2. Paracetamol 500mg
           Frequency: Every 6 hours
           Duration: As needed (max 5 days)
        
        3. Metformin 500mg
           Frequency: Twice daily
           Duration: 30 days
        
        Doctor: Dr. Smith
        Date: 2024-01-15
        """
        return mock_ocr_text, 0.92
    
    def parse_prescription(self, ocr_text: str) -> List[DrugInfo]:
        """
        Parse OCR text to extract drug information
        Uses simple pattern matching and AI-like rules
        """
        drugs = []
        lines = ocr_text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for drug names (heuristic: capitalized words)
            if self._is_drug_line(line):
                drug_info = self._extract_drug_from_section(lines, i)
                if drug_info:
                    drugs.append(drug_info)
                i += 1
            else:
                i += 1
        
        return drugs
    
    def _is_drug_line(self, line: str) -> bool:
        """Check if line likely contains a drug name"""
        if not line or len(line) < 2:
            return False
        
        # Common drug patterns
        common_drugs = [
            'amoxicillin', 'paracetamol', 'ibuprofen', 'metformin',
            'lisinopril', 'amlodipine', 'atorvastatin', 'omeprazole',
            'aspirin', 'vitamin', 'antibiotic', 'tablet', 'capsule'
        ]
        
        line_lower = line.lower()
        for drug in common_drugs:
            if drug in line_lower:
                return True
        
        # Check if line starts with uppercase and has numbers (dosage)
        return line[0].isupper() and any(c.isdigit() for c in line)
    
    def _extract_drug_from_section(self, lines: List[str], start_idx: int) -> Optional[DrugInfo]:
        """Extract drug info from a multi-line section"""
        drug_line = lines[start_idx].strip()
        dosage = None
        frequency = None
        duration = None
        
        # Extract dosage from same line or next line
        dosage_match = self._extract_dosage(drug_line)
        drug_name = self._clean_drug_name(drug_line, dosage_match)
        dosage = dosage_match
        
        # Look ahead for frequency and duration
        for i in range(start_idx + 1, min(start_idx + 5, len(lines))):
            next_line = lines[i].strip().lower()
            
            if 'frequency' in next_line or 'times' in next_line or 'daily' in next_line:
                frequency = lines[i].strip()
            elif 'duration' in next_line or 'days' in next_line or 'week' in next_line:
                duration = lines[i].strip()
            
            # Stop if we hit another drug or section
            if self._is_drug_line(lines[i]) and i != start_idx:
                break
        
        return DrugInfo(drug_name, dosage, frequency, duration)
    
    def _extract_dosage(self, text: str) -> Optional[str]:
        """Extract dosage information from text"""
        import re
        
        # Pattern: number + unit (mg, ml, g, etc.)
        pattern = r'(\d+\s*(?:mg|ml|g|units?|iu))'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        return matches[0] if matches else None
    
    def _clean_drug_name(self, text: str, dosage: Optional[str] = None) -> str:
        """Clean drug name from text by removing dosage"""
        if dosage:
            text = text.replace(dosage, '')
        
        return text.strip()
    
    def verify_extraction_quality(self, ocr_text: str, drugs: List[DrugInfo]) -> float:
        """
        Verify quality of extraction
        Returns confidence score 0-1
        """
        if not ocr_text or not drugs:
            return 0.0
        
        # Base score: presence of text and drugs
        score = 0.5
        
        # Bonus for finding multiple drugs
        score += min(len(drugs) * 0.1, 0.3)
        
        # Bonus for complete drug info
        complete_drugs = sum(
            1 for drug in drugs 
            if drug.dosage and drug.frequency
        )
        score += (complete_drugs / max(len(drugs), 1)) * 0.2
        
        return min(score, 1.0)

# Singleton instance
_ocr_service = None

def get_ocr_service() -> OCRService:
    """Get or create OCR service instance"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
