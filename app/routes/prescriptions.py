"""
Prescription Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List
import tempfile
import os
from ..models import (
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse,
    OCRResponse, DrugInput, SuccessResponse
)
from ..services.database_service import get_db_service
from ..services.ocr_service import get_ocr_service
from ..services.drug_service import get_drug_service

router = APIRouter(prefix="/api/prescriptions", tags=["prescriptions"])

@router.post("/{user_id}", response_model=PrescriptionResponse)
def create_prescription(user_id: str, prescription_data: PrescriptionCreate):
    """Create a new prescription"""
    db_service = get_db_service()
    
    # Verify user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create prescription
    prescription_id = db_service.create_prescription(
        user_id=user_id,
        image_url=prescription_data.image_url,
        ocr_text=prescription_data.ocr_text
    )
    
    prescription = db_service.get_prescription(prescription_id)
    prescription['drugs'] = []
    
    return PrescriptionResponse(**prescription)

@router.post("/{user_id}/upload", response_model=OCRResponse)
async def upload_prescription_image(
    user_id: str,
    file: UploadFile = File(...),
    auto_match: bool = Form(True)
):
    """Upload prescription image and extract text via OCR"""
    db_service = get_db_service()
    ocr_service = get_ocr_service()
    drug_service = get_drug_service()
    
    # Verify user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Extract text from image
        ocr_text, confidence = ocr_service.extract_text_from_image(tmp_path)
        
        # Parse drugs from OCR text (with AI fallback for tablet images)
        drugs = await ocr_service.parse_prescription(ocr_text, tmp_path)
        
        # Create prescription in database
        prescription_id = db_service.create_prescription(
            user_id=user_id,
            image_url=file.filename,
            ocr_text=ocr_text
        )
        
        # Update with OCR confidence
        db_service.update_prescription(prescription_id, {
            'ocr_confidence': confidence,
            'status': 'processed'
        })
        
        # Add drugs to prescription and match against Emdex
        drug_results = []
        for drug in drugs:
            # Add to prescription
            db_service.add_drug_to_prescription(prescription_id, drug.to_dict())
            
            # Match against Emdex if enabled
            if auto_match:
                match = await drug_service.match_drug_emdex(drug.name, drug.dosage)
                if match:
                    drug.emdex_id = match.emdex_id
            
            drug_results.append(drug.to_dict())
        
        # Cleanup temp file
        os.unlink(tmp_path)
        
        return OCRResponse(
            text=ocr_text,
            confidence=confidence,
            drugs=[DrugInput(**d) for d in drug_results]
        )
    
    except Exception as e:
        # Cleanup temp file on error
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=List[PrescriptionResponse])
def get_user_prescriptions(user_id: str):
    """Get all prescriptions for a user"""
    db_service = get_db_service()
    
    # Verify user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    prescriptions = db_service.get_user_prescriptions(user_id)
    
    # Attach drugs to each prescription
    for prescription in prescriptions:
        drugs = db_service.get_prescription_drugs(prescription['id'])
        prescription['drugs'] = drugs
    
    return [PrescriptionResponse(**p) for p in prescriptions]

@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription(prescription_id: int):
    """Get prescription by ID"""
    db_service = get_db_service()
    
    prescription = db_service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Attach drugs
    drugs = db_service.get_prescription_drugs(prescription_id)
    prescription['drugs'] = drugs
    
    return PrescriptionResponse(**prescription)

@router.put("/{prescription_id}", response_model=PrescriptionResponse)
def update_prescription(prescription_id: int, prescription_data: PrescriptionUpdate):
    """Update prescription"""
    db_service = get_db_service()
    
    prescription = db_service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    # Update prescription
    updates = {k: v for k, v in prescription_data.model_dump().items() if v is not None}
    db_service.update_prescription(prescription_id, updates)
    
    # Return updated prescription
    updated = db_service.get_prescription(prescription_id)
    drugs = db_service.get_prescription_drugs(prescription_id)
    updated['drugs'] = drugs
    
    return PrescriptionResponse(**updated)

@router.post("/{prescription_id}/drugs", response_model=SuccessResponse)
def add_drug_to_prescription(prescription_id: int, drug_data: DrugInput):
    """Add a drug to prescription"""
    db_service = get_db_service()
    
    prescription = db_service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    try:
        drug_id = db_service.add_drug_to_prescription(prescription_id, drug_data.model_dump())
        return SuccessResponse(
            success=True,
            message="Drug added to prescription",
            data={'drug_id': drug_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{prescription_id}", response_model=SuccessResponse)
def delete_prescription(prescription_id: int):
    """Delete prescription"""
    db_service = get_db_service()
    
    prescription = db_service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    try:
        db_service.execute_update(
            "DELETE FROM prescriptions WHERE id = ?",
            (prescription_id,)
        )
        
        return SuccessResponse(
            success=True,
            message="Prescription deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
