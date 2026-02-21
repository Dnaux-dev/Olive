"""
Medication Management API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models import (
    MedicationCreate, MedicationUpdate, MedicationResponse,
    SuccessResponse
)
from ..services.database_service import get_db_service
from ..services.firebase_service import get_firebase_service
from ..services.reminder_service import get_reminder_service
import json

router = APIRouter(prefix="/api/medications", tags=["medications"])

@router.post("/{user_id}", response_model=MedicationResponse)
def create_medication(user_id: str, medication_data: MedicationCreate):
    """Create a new medication for user"""
    db_service = get_db_service()
    firebase_service = get_firebase_service()
    reminder_service = get_reminder_service()
    
    # Verify user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Prepare medication data
        med_dict = medication_data.model_dump()
        med_dict['user_id'] = user_id
        med_dict['reminder_times'] = json.dumps(med_dict.get('reminder_times', []))
        med_dict['side_effects'] = json.dumps(med_dict.get('side_effects', []))
        
        # Create medication in SQLite
        medication_id = db_service.create_medication(med_dict)
        
        # Schedule reminders if reminder times provided
        if medication_data.reminder_times:
            reminder_service.schedule_reminder(medication_id, medication_data.reminder_times)
        
        # Sync to Firebase
        medication = db_service.get_medication(medication_id)
        firebase_service.sync_user_medications(user_id, [medication])
        
        return MedicationResponse(**medication)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{medication_id}", response_model=MedicationResponse)
def get_medication(medication_id: int):
    """Get medication by ID"""
    db_service = get_db_service()
    
    medication = db_service.get_medication(medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    return MedicationResponse(**medication)

@router.get("/user/{user_id}", response_model=List[MedicationResponse])
def get_user_medications(user_id: str, status: Optional[str] = "active"):
    """Get all medications for a user"""
    db_service = get_db_service()
    
    # Verify user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    medications = db_service.get_user_medications(user_id, status=status)
    return [MedicationResponse(**m) for m in medications]

@router.put("/{medication_id}", response_model=MedicationResponse)
def update_medication(medication_id: int, medication_data: MedicationUpdate):
    """Update medication"""
    db_service = get_db_service()
    firebase_service = get_firebase_service()
    
    medication = db_service.get_medication(medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    try:
        # Prepare updates
        updates = medication_data.model_dump(exclude_unset=True)
        
        # Handle JSON fields
        if 'reminder_times' in updates:
            updates['reminder_times'] = json.dumps(updates['reminder_times'])
        if 'side_effects' in updates:
            updates['side_effects'] = json.dumps(updates['side_effects'])
        
        # Update in SQLite
        db_service.update_medication(medication_id, updates)
        
        # Sync to Firebase
        updated = db_service.get_medication(medication_id)
        firebase_service.sync_user_medications(
            medication['user_id'],
            [updated]
        )
        
        return MedicationResponse(**updated)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{medication_id}", response_model=SuccessResponse)
def delete_medication(medication_id: int):
    """Delete medication (soft delete via status)"""
    db_service = get_db_service()
    
    medication = db_service.get_medication(medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    try:
        # Mark as deleted rather than hard delete to preserve history
        db_service.update_medication(medication_id, {'status': 'stopped'})
        
        return SuccessResponse(
            success=True,
            message="Medication stopped"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{medication_id}/side-effect", response_model=SuccessResponse)
def add_side_effect(medication_id: int, effect: str):
    """Add reported side effect to medication"""
    db_service = get_db_service()
    
    medication = db_service.get_medication(medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    try:
        side_effects = json.loads(medication.get('side_effects', '[]'))
        if effect not in side_effects:
            side_effects.append(effect)
            db_service.update_medication(medication_id, {
                'side_effects': json.dumps(side_effects)
            })
        
        return SuccessResponse(
            success=True,
            message="Side effect recorded"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{medication_id}/compliance", response_model=MedicationResponse)
def record_medication_taken(medication_id: int):
    """Record that user took their medication"""
    db_service = get_db_service()
    
    medication = db_service.get_medication(medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    try:
        # Increment reminders sent counter
        reminders_sent = medication.get('reminders_sent', 0) + 1
        db_service.update_medication(medication_id, {
            'reminders_sent': reminders_sent
        })
        
        updated = db_service.get_medication(medication_id)
        return MedicationResponse(**updated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
