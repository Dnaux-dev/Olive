"""
User Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models import UserCreate, UserUpdate, UserResponse, SuccessResponse
from ..services.database_service import get_db_service
from ..services.firebase_service import get_firebase_service
import uuid

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate):
    """Create a new user"""
    db_service = get_db_service()
    firebase_service = get_firebase_service()
    
    # Check if user already exists
    existing = db_service.get_user_by_phone(user_data.phone_number)
    if existing:
        raise HTTPException(status_code=400, detail="User with this phone number already exists")
    
    # Create user in SQLite
    user_data_dict = user_data.model_dump()
    user_data_dict['id'] = str(uuid.uuid4())
    
    user_id = db_service.create_user(user_data_dict)
    
    # Create Firebase structure
    firebase_service.create_user_structure(user_id)
    
    # Return created user
    user = db_service.get_user(user_id)
    return UserResponse(**user)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    """Get user by ID"""
    db_service = get_db_service()
    
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user)

@router.get("/phone/{phone_number}", response_model=UserResponse)
def get_user_by_phone(phone_number: str):
    """Get user by phone number"""
    db_service = get_db_service()
    
    user = db_service.get_user_by_phone(phone_number)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user_data: UserUpdate):
    """Update user information"""
    db_service = get_db_service()
    firebase_service = get_firebase_service()
    
    # Check user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update in SQLite
    updates = {k: v for k, v in user_data.model_dump().items() if v is not None}
    db_service.update_user(user_id, updates)
    
    # Sync to Firebase
    updated_user = db_service.get_user(user_id)
    firebase_service.sync_user_profile(user_id, updated_user)
    
    return UserResponse(**updated_user)

@router.delete("/{user_id}", response_model=SuccessResponse)
def delete_user(user_id: str):
    """Delete user and all associated data"""
    db_service = get_db_service()
    firebase_service = get_firebase_service()
    
    # Check user exists
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Delete from SQLite (cascade deletes related data)
        db_service.execute_update(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        
        # Delete from Firebase
        firebase_service.delete_user_data(user_id)
        
        return SuccessResponse(
            success=True,
            message="User deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/verify-phone", response_model=SuccessResponse)
def verify_phone(user_id: str):
    """Send verification code to user's phone"""
    from ..services.whatsapp_service import get_whatsapp_service
    
    db_service = get_db_service()
    whatsapp_service = get_whatsapp_service()
    
    user = db_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Send verification code
    result = whatsapp_service.send_verification_request(user['phone_number'])
    
    if result.get('success'):
        return SuccessResponse(
            success=True,
            message="Verification code sent"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification code"
        )
