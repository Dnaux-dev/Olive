"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ==================== User Models ====================
class UserCreate(BaseModel):
    phone_number: str
    email: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    language_preference: Optional[str] = 'english'
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    language_preference: Optional[str] = None
    reminders_enabled: Optional[bool] = None
    email_reminders_enabled: Optional[bool] = None
    password: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    phone_number: str
    email: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    language_preference: Optional[str] = 'english'
    reminders_enabled: bool
    email_reminders_enabled: bool
    email_verified: bool
    created_at: str

class TokenResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

# ==================== Verification Models ====================
class DrugVerificationRequest(BaseModel):
    reg_number: str

class DrugVerificationResponse(BaseModel):
    status: str  # verified, suspicious, invalid_format
    message: str
    product_details: Optional[Dict[str, Any]] = None
    verification_tips: List[str]

# ==================== Prescription Models ====================
class DrugInput(BaseModel):
    drug_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    emdex_id: Optional[str] = None

class PrescriptionCreate(BaseModel):
    image_url: Optional[str] = None
    ocr_text: Optional[str] = None

class PrescriptionUpdate(BaseModel):
    status: Optional[str] = None
    verified_by_user: Optional[bool] = None

class PrescriptionResponse(BaseModel):
    id: int
    user_id: str
    image_url: Optional[str]
    ocr_text: Optional[str]
    ocr_confidence: Optional[float]
    status: str
    verified_by_user: bool
    created_at: str
    drugs: Optional[List[DrugInput]] = []

# ==================== Medication Models ====================
class MedicationCreate(BaseModel):
    prescription_id: Optional[int] = None
    drug_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: str  # ISO format
    end_date: Optional[str] = None
    reminder_times: List[str] = Field(default_factory=list)  # HH:MM format
    side_effects: Optional[List[str]] = None

class MedicationUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    end_date: Optional[str] = None
    reminder_times: Optional[List[str]] = None
    status: Optional[str] = None  # active, completed, stopped
    side_effects: Optional[List[str]] = None

class MedicationResponse(BaseModel):
    id: int
    user_id: str
    prescription_id: Optional[int]
    drug_name: str
    dosage: Optional[str]
    frequency: Optional[str]
    start_date: str
    end_date: Optional[str]
    reminder_times: Optional[str]
    reminders_sent: int
    status: str
    side_effects: Optional[str]
    created_at: str

# ==================== Reminder Models ====================
class ReminderCreate(BaseModel):
    medication_id: int
    reminder_datetime: str  # ISO format

class ReminderUpdate(BaseModel):
    delivery_status: Optional[str] = None
    sent: Optional[bool] = None

class ReminderResponse(BaseModel):
    id: int
    user_id: str
    medication_id: int
    reminder_datetime: str
    sent: bool
    delivery_status: str
    whatsapp_message_id: Optional[str]
    created_at: str
    drug_name: Optional[str] = None
    dosage: Optional[str] = None

class ReminderStatsResponse(BaseModel):
    total: int
    sent: int
    taken: int
    pending: int

# ==================== Drug Models ====================
class GenericResponse(BaseModel):
    name: str
    price_naira: float
    manufacturer: str
    savings: float

class DrugResponse(BaseModel):
    emdex_id: str
    name: str
    generic_name: Optional[str]
    price_naira: float
    manufacturer: str
    generics: List[GenericResponse] = []

class DrugSearchResponse(BaseModel):
    results: List[DrugResponse]

# ==================== Pill Models ====================
class PillVerificationResponse(BaseModel):
    matched: bool
    drug_name: Optional[str] = None
    confidence: float

# ==================== OCR Models ====================
class OCRResponse(BaseModel):
    text: str
    confidence: float
    drugs: List[DrugInput]

# ==================== WhatsApp Models ====================
class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[Dict[str, Any]]

class WhatsAppMessage(BaseModel):
    from_phone: str
    type: str
    text: Optional[str] = None
    image_id: Optional[str] = None
    message_id: str

# ==================== Response Models ====================
class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

# ==================== Batch Models ====================
class RemindersResult(BaseModel):
    sent: int
    failed: int
    errors: List[Dict[str, Any]] = []
# ==================== Doctor Models ====================
class DoctorCategory(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

class Doctor(BaseModel):
    id: str
    name: str
    specialty: str
    category_id: str
    experience_years: int
    rating: float
    review_count: int
    availability: str
    bio: str
    profile_image_url: Optional[str] = None
    is_verified: bool = True
    location: Optional[str] = None
    consultation_fee: Optional[float] = None

class DoctorResponse(BaseModel):
    doctors: List[Doctor]
    total_count: int
