"""
User Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from ..models import UserCreate, UserUpdate, UserResponse, SuccessResponse, LoginRequest, TokenResponse
from ..services.database_service import get_db_service
from ..services.firebase_service import get_firebase_service
from ..services.auth_service import create_access_token
import uuid

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/", response_model=TokenResponse)
def create_user(user_data: UserCreate, background_tasks: BackgroundTasks):
    """Create a new user"""
    db_service = get_db_service()
    firebase_service = get_firebase_service()
    
    # Check if user already exists
    if user_data.email:
        existing = db_service.get_user_by_email(user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")
    
    existing_phone = db_service.get_user_by_phone(user_data.phone_number)
    if existing_phone:
        raise HTTPException(status_code=400, detail="User with this phone number already exists")
    
    # Create user in SQLite
    user_data_dict = user_data.model_dump()
    user_id = db_service.create_user(user_data_dict)
    
    # Create Firebase structure
    firebase_service.create_user_structure(user_id)
    
    # Automatically trigger email verification if email provided
    if user_data.email:
        background_tasks.add_task(initiate_email_verification, user_id)
    
    # Return created user with token
    user_data = db_service.get_user(user_id)
    user_res = UserResponse(**user_data)
    access_token = create_access_token(data={"sub": user_id})
    
    return TokenResponse(user=user_res, access_token=access_token)

async def initiate_email_verification(user_id: str):
    """Helper to send verification OTP (Async)"""
    from ..services.email_service import get_email_service
    import random
    
    db_service = get_db_service()
    email_service = get_email_service()
    
    user = db_service.get_user(user_id)
    if not user or not user.get('email'):
        return False
    
    # Generate random 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    
    # Store OTP in audit logs
    db_service.log_action(
        user_id=user_id,
        action="email_otp_generated",
        details={"otp": otp_code}
    )
    
    return await email_service.send_otp(user['email'], otp_code, user.get('name', 'User'))

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    """Login with email and password"""
    db_service = get_db_service()
    
    user = db_service.get_user_by_email(login_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not db_service.verify_password(login_data.password, user.get('password_hash')):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_res = UserResponse(**user)
    access_token = create_access_token(data={"sub": user['id']})
    
    return TokenResponse(user=user_res, access_token=access_token)

@router.post("/logout", response_model=SuccessResponse)
def logout():
    """Logout endpoint (client should discard the token)"""
    return SuccessResponse(success=True, message="Logged out successfully")

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

@router.post("/{user_id}/verify-email", response_model=SuccessResponse)
async def verify_email(user_id: str):
    """Manually trigger verification OTP to user's email (Async)"""
    if await initiate_email_verification(user_id):
        return SuccessResponse(
            success=True,
            message="Verification email sent"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email"
        )

@router.post("/{user_id}/confirm-email", response_model=SuccessResponse)
def confirm_email(user_id: str, otp_code: str):
    """Confirm email OTP"""
    db_service = get_db_service()
    
    # Check latest OTP from audit logs
    logs = db_service.execute_query(
        """SELECT details FROM audit_logs 
           WHERE user_id = ? AND action = 'email_otp_generated' 
           ORDER BY timestamp DESC LIMIT 1""",
        (user_id,),
        fetch_one=True
    )
    
    if not logs:
        raise HTTPException(status_code=400, detail="No OTP requested")
    
    import json
    saved_otp = json.loads(logs['details']).get('otp')
    
    if saved_otp == otp_code:
        db_service.verify_email(user_id)
        return SuccessResponse(
            success=True,
            message="Email verified successfully"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
