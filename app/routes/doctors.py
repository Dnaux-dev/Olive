"""
Doctor API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..models import Doctor, DoctorResponse, SuccessResponse
from ..services.doctor_service import get_doctor_service

router = APIRouter(prefix="/api/doctors", tags=["doctors"])

@router.get("/", response_model=DoctorResponse)
def get_doctors(
    specialty: Optional[str] = None, 
    category_id: Optional[str] = None
):
    """
    Get all verified doctors.
    Optional filters: specialty, category_id.
    """
    doctor_service = get_doctor_service()
    if specialty or category_id:
        doctors = doctor_service.search_doctors(specialty, category_id)
    else:
        doctors = doctor_service.get_all_doctors()
    
    return DoctorResponse(
        doctors=doctors,
        total_count=len(doctors)
    )

@router.get("/categories", response_model=SuccessResponse)
def get_doctor_categories():
    """Get list of doctor categories"""
    categories = [
        {"id": "maternal_health", "name": "Maternal Health", "description": "Specialists for pregnancy and childbirth"},
        {"id": "child_health", "name": "Child Health", "description": "Pediatricians and infant care specialists"},
        {"id": "general_practice", "name": "General Practice", "description": "Family physicians for general health concerns"}
    ]
    return SuccessResponse(
        success=True,
        data={"categories": categories}
    )

@router.get("/{doctor_id}", response_model=Doctor)
def get_doctor_details(doctor_id: str):
    """Get details for a specific doctor"""
    doctor_service = get_doctor_service()
    doctor = doctor_service.get_doctor_by_id(doctor_id)
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    return Doctor(**doctor)
