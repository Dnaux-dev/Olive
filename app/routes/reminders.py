"""
Reminder Management API Endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models import (
    ReminderCreate, ReminderUpdate, ReminderResponse,
    ReminderStatsResponse, RemindersResult, SuccessResponse
)
from ..services.reminder_service import get_reminder_service
from ..services.database_service import get_db_service

router = APIRouter(prefix="/api/reminders", tags=["reminders"])

@router.post("/{medication_id}", response_model=List[ReminderResponse])
def schedule_reminders(medication_id: int, reminder_times: List[str]):
    """Schedule reminders for a medication"""
    db_service = get_db_service()
    reminder_service = get_reminder_service()
    
    # Verify medication exists
    medication = db_service.get_medication(medication_id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    try:
        reminder_ids = reminder_service.schedule_reminder(medication_id, reminder_times)
        
        reminders = [
            db_service.execute_query(
                """SELECT r.*, m.drug_name, m.dosage
                   FROM reminders r
                   JOIN medications m ON r.medication_id = m.id
                   WHERE r.id = ?""",
                (rid,),
                fetch_one=True
            )
            for rid in reminder_ids
        ]
        
        return [ReminderResponse(**r) for r in reminders if r]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(reminder_id: int):
    """Get reminder by ID"""
    db_service = get_db_service()
    
    reminder = db_service.execute_query(
        """SELECT r.*, m.drug_name, m.dosage
           FROM reminders r
           JOIN medications m ON r.medication_id = m.id
           WHERE r.id = ?""",
        (reminder_id,),
        fetch_one=True
    )
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    return ReminderResponse(**reminder)

@router.get("/user/{user_id}", response_model=List[ReminderResponse])
def get_user_reminders(user_id: str, status: Optional[str] = "pending", days: Optional[int] = 7):
    """Get reminders for a user"""
    db_service = get_db_service()
    reminder_service = get_reminder_service()
    
    # Verify user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    reminders = reminder_service.get_user_reminders(user_id, status=status, days=days)
    return [ReminderResponse(**r) for r in reminders]

@router.get("/user/{user_id}/stats", response_model=ReminderStatsResponse)
def get_user_reminder_stats(user_id: str):
    """Get reminder statistics for user"""
    db_service = get_db_service()
    reminder_service = get_reminder_service()
    
    # Verify user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    stats = reminder_service.get_reminder_stats(user_id)
    return ReminderStatsResponse(**stats)

@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(reminder_id: int, reminder_data: ReminderUpdate):
    """Update reminder status"""
    db_service = get_db_service()
    
    reminder = db_service.execute_query(
        """SELECT r.*, m.drug_name, m.dosage
           FROM reminders r
           JOIN medications m ON r.medication_id = m.id
           WHERE r.id = ?""",
        (reminder_id,),
        fetch_one=True
    )
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    try:
        updates = {k: v for k, v in reminder_data.model_dump().items() if v is not None}
        db_service.update_reminder(reminder_id, updates)
        
        updated = db_service.execute_query(
            """SELECT r.*, m.drug_name, m.dosage
               FROM reminders r
               JOIN medications m ON r.medication_id = m.id
               WHERE r.id = ?""",
            (reminder_id,),
            fetch_one=True
        )
        
        return ReminderResponse(**updated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{reminder_id}/send", response_model=SuccessResponse)
def send_reminder(reminder_id: int):
    """Send a reminder"""
    db_service = get_db_service()
    reminder_service = get_reminder_service()
    
    reminder = db_service.execute_query(
        "SELECT * FROM reminders WHERE id = ?",
        (reminder_id,),
        fetch_one=True
    )
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    try:
        result = reminder_service.send_reminder(reminder_id)
        
        if result['success']:
            return SuccessResponse(
                success=True,
                message="Reminder sent successfully",
                data={'message_id': result.get('message_id')}
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pending/send-all", response_model=RemindersResult)
def send_all_due_reminders():
    """Send all reminders that are currently due"""
    reminder_service = get_reminder_service()
    
    try:
        results = reminder_service.send_all_due_reminders()
        return RemindersResult(**results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{reminder_id}/snooze", response_model=SuccessResponse)
def snooze_reminder(reminder_id: int, minutes: int = 5):
    """Snooze a reminder"""
    db_service = get_db_service()
    reminder_service = get_reminder_service()
    
    reminder = db_service.execute_query(
        "SELECT * FROM reminders WHERE id = ?",
        (reminder_id,),
        fetch_one=True
    )
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    try:
        success = reminder_service.snooze_reminder(reminder_id, minutes)
        
        if success:
            return SuccessResponse(
                success=True,
                message=f"Reminder snoozed for {minutes} minutes"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to snooze reminder")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{reminder_id}/taken", response_model=SuccessResponse)
def mark_reminder_taken(reminder_id: int):
    """Mark reminder as taken by user"""
    db_service = get_db_service()
    reminder_service = get_reminder_service()
    
    reminder = db_service.execute_query(
        "SELECT * FROM reminders WHERE id = ?",
        (reminder_id,),
        fetch_one=True
    )
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    try:
        success = reminder_service.mark_reminder_taken(reminder_id)
        
        if success:
            return SuccessResponse(
                success=True,
                message="Reminder marked as taken"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to mark reminder")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{reminder_id}", response_model=SuccessResponse)
def delete_reminder(reminder_id: int):
    """Delete a reminder"""
    db_service = get_db_service()
    
    reminder = db_service.execute_query(
        "SELECT * FROM reminders WHERE id = ?",
        (reminder_id,),
        fetch_one=True
    )
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    try:
        db_service.execute_update(
            "DELETE FROM reminders WHERE id = ?",
            (reminder_id,)
        )
        
        return SuccessResponse(
            success=True,
            message="Reminder deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
