# Olive-AI Backend Setup Guide

Complete step-by-step guide to set up and run the Olive-AI backend.

## Project Structure Overview

```
medi-sync-backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration from environment
│   ├── models.py                  # Pydantic request/response models
│   ├── routes/                    # API endpoint implementations
│   │   ├── __init__.py
│   │   ├── users.py              # User CRUD operations (CREATE, READ, UPDATE, DELETE)
│   │   ├── prescriptions.py       # Prescription upload, OCR, storage
│   │   ├── medications.py         # Medication management with Firebase sync
│   │   ├── reminders.py           # Reminder scheduling and delivery tracking
│   │   ├── drugs.py               # Drug database search and price comparison
│   │   └── whatsapp.py            # WhatsApp webhook and message handling
│   ├── services/                  # Business logic and external API integration
│   │   ├── __init__.py
│   │   ├── database_service.py    # SQLite connection pool and queries
│   │   ├── firebase_service.py    # Firebase Realtime DB operations
│   │   ├── ocr_service.py         # Google Cloud Vision integration + fallback
│   │   ├── drug_service.py        # Emdex API + local caching
│   │   ├── pill_service.py        # Pill image matching with features
│   │   ├── whatsapp_service.py    # WhatsApp Cloud API messaging
│   │   └── reminder_service.py    # Reminder logic and scheduling
│   └── tasks/                     # Background job definitions
│       ├── __init__.py
│       └── reminders.py           # APScheduler for periodic reminder checks
│
├── scripts/
│   ├── __init__.py
│   ├── init_db.py                 # SQLite schema and indexes creation
│   └── init_firebase.py           # Firebase Realtime DB structure setup
│
├── config.py                      # Environment configuration (pydantic-settings)
├── requirements.txt               # Python dependencies
├── .env.example                   # Template for environment variables
├── README.md                      # Project documentation
├── BACKEND_SETUP.md              # This file
└── .gitignore                     # Git ignore patterns
```

## 1. Initial Setup

### Step 1.1: Clone or Initialize Project
```bash
# If starting fresh
mkdir medi-sync-backend
cd medi-sync-backend

# Or clone existing repo
git clone <repo-url>
cd medi-sync-backend
```

### Step 1.2: Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 1.3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 1.4: Create Data Directories
```bash
mkdir -p data
mkdir -p logs
```

## 2. Configuration

### Step 2.1: Copy Environment Template
```bash
cp .env.example .env
```

### Step 2.2: Get External API Keys

#### Google Cloud Vision API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable "Cloud Vision API"
4. Create service account
5. Download JSON key file
6. Set `GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json`

#### Firebase Realtime Database
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create new project
3. Enable Realtime Database
4. Download service account key
5. Set `FIREBASE_SERVICE_ACCOUNT_KEY_PATH=path/to/key.json`
6. Copy database URL (looks like `https://PROJECT.firebaseio.com`)
7. Set `FIREBASE_DATABASE_URL` in .env

#### WhatsApp Cloud API
1. Go to [Meta Business Suite](https://business.facebook.com)
2. Create WhatsApp Business App
3. Get phone number ID and access token
4. Set webhook verify token (any random string you create)
5. Add to `.env`:
   ```
   WHATSAPP_PHONE_NUMBER_ID=1234567890
   WHATSAPP_ACCESS_TOKEN=EAAB...
   WHATSAPP_WEBHOOK_TOKEN=your_webhook_token
   ```

#### Emdex API (Optional - Uses Mocks)
1. Register at Emdex
2. Get API key
3. Set `EMDEX_API_KEY` in .env

### Step 2.3: Configure Environment Variables
Edit `.env` file:
```env
# Firebase
FIREBASE_API_KEY=your_api_key
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./firebase-key.json

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./google-key.json
GCP_PROJECT_ID=your_gcp_project

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_WEBHOOK_TOKEN=webhook_verify_token

# App
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-super-secret-key-change-in-production
DATABASE_PATH=./data/medi_sync.db
```

## 3. Database Setup

### Step 3.1: Initialize SQLite Schema
```bash
python scripts/init_db.py
```

This creates:
- 8 SQLite tables with proper relationships
- Indexes on frequently queried columns
- Foreign key constraints

**Tables Created:**
- `users` - User profiles
- `prescriptions` - Scanned prescription documents
- `prescription_drugs` - Junction table for drugs in prescriptions
- `medications` - Active user medications
- `pills` - Pill image database
- `drug_database` - Emdex drug cache
- `reminders` - Scheduled reminders
- `audit_logs` - Activity audit trail

### Step 3.2: Initialize Firebase (If Using)
```bash
python scripts/init_firebase.py
```

This creates the Firebase Realtime DB structure:
```
/users/{userId}/profile       → User profile sync
/users/{userId}/medications   → Real-time medications
/users/{userId}/reminders     → Pending reminders
/sync_logs                     → Sync audit trail
```

## 4. Service Implementations

### Database Service
**File**: `app/services/database_service.py`

Provides:
- SQLite connection pooling with context managers
- CRUD operations for all entities
- Query building and parameterized queries
- Audit logging of changes

Example usage:
```python
from app.services.database_service import get_db_service

db = get_db_service()
user = db.get_user("user_id_123")
medications = db.get_user_medications("user_id_123", status="active")
```

### Firebase Service
**File**: `app/services/firebase_service.py`

Provides:
- User profile sync to Firebase
- Real-time medication updates
- Reminder push notifications
- Sync tracking and audit logs

Example usage:
```python
from app.services.firebase_service import get_firebase_service

firebase = get_firebase_service()
firebase.sync_user_medications("user_id", medications_list)
firebase.push_reminder("user_id", reminder_id, reminder_data)
```

### OCR Service
**File**: `app/services/ocr_service.py`

Features:
- Google Cloud Vision API integration
- Prescription text extraction with confidence scores
- Drug parsing from OCR text (heuristic-based)
- Fallback mock data for development

Example usage:
```python
from app.services.ocr_service import get_ocr_service

ocr = get_ocr_service()
text, confidence = ocr.extract_text_from_image("prescription.jpg")
drugs = ocr.parse_prescription(text)
```

### Drug Service
**File**: `app/services/drug_service.py`

Features:
- Drug name matching against Emdex database
- Generic alternatives lookup
- Price comparison with savings calculation
- Local SQLite cache to reduce API calls
- Fallback mock data

Example usage:
```python
from app.services.drug_service import get_drug_service

drug_svc = get_drug_service()
drug_match = drug_svc.match_drug_emdex("Amoxicillin", "500mg")
generics = drug_match.generics  # List of alternatives
```

### Pill Service
**File**: `app/services/pill_service.py`

Features:
- Pill image feature extraction (shape, color, size)
- Matching against pill database
- Confidence scoring
- Manual pill database management

Example usage:
```python
from app.services.pill_service import get_pill_service

pill_svc = get_pill_service()
verification = pill_svc.verify_pill(image_bytes)
# Returns: {matched: True, drug_name: "Amoxicillin", confidence: 0.85}
```

### WhatsApp Service
**File**: `app/services/whatsapp_service.py`

Features:
- WhatsApp Cloud API integration
- Message sending (text and template)
- Webhook verification and parsing
- Media download from WhatsApp
- Localized reminder messages

Example usage:
```python
from app.services.whatsapp_service import get_whatsapp_service

wa = get_whatsapp_service()
result = wa.send_reminder("+2348012345678", {"drug_name": "Amoxicillin"})
# Returns: {success: True, message_id: "wamid.XXX"}
```

### Reminder Service
**File**: `app/services/reminder_service.py`

Features:
- Reminder scheduling (creates entries for medication duration)
- Due reminder retrieval
- WhatsApp delivery integration
- Reminder status tracking (pending, sent, taken)
- Compliance statistics
- Snooze functionality

Example usage:
```python
from app.services.reminder_service import get_reminder_service

reminder_svc = get_reminder_service()
reminder_ids = reminder_svc.schedule_reminder(med_id, ["09:00", "18:00"])
results = reminder_svc.send_all_due_reminders()
stats = reminder_svc.get_reminder_stats("user_id")
```

## 5. API Routes

### User Routes (`/api/users`)
```
POST   /api/users                    Create new user
GET    /api/users/{user_id}          Get user by ID
GET    /api/users/phone/{phone}      Get user by phone
PUT    /api/users/{user_id}          Update user
DELETE /api/users/{user_id}          Delete user + all data
POST   /api/users/{user_id}/verify-phone  Send verification code
```

### Prescription Routes (`/api/prescriptions`)
```
POST   /api/prescriptions/{user_id}           Create prescription
POST   /api/prescriptions/{user_id}/upload    Upload image, extract OCR, extract drugs
GET    /api/prescriptions/{user_id}           Get all user prescriptions
GET    /api/prescriptions/{id}                Get prescription details
PUT    /api/prescriptions/{id}                Update prescription
DELETE /api/prescriptions/{id}                Delete prescription
POST   /api/prescriptions/{id}/drugs          Add drug to prescription
```

### Medication Routes (`/api/medications`)
```
POST   /api/medications/{user_id}                     Create medication
GET    /api/medications/{med_id}                      Get medication
GET    /api/medications/user/{user_id}               Get user's medications
PUT    /api/medications/{med_id}                      Update medication
DELETE /api/medications/{med_id}                      Stop medication
POST   /api/medications/{med_id}/side-effect          Report side effect
POST   /api/medications/{med_id}/compliance           Record medication taken
```

### Reminder Routes (`/api/reminders`)
```
POST   /api/reminders/{med_id}                 Schedule reminders for times
GET    /api/reminders/{id}                     Get reminder details
GET    /api/reminders/user/{user_id}           Get user's reminders
GET    /api/reminders/user/{user_id}/stats     Get reminder stats
PUT    /api/reminders/{id}                     Update reminder status
POST   /api/reminders/{id}/send                Send reminder immediately
POST   /api/reminders/{id}/snooze              Snooze reminder N minutes
POST   /api/reminders/{id}/taken               Mark as taken
DELETE /api/reminders/{id}                     Delete reminder
POST   /api/reminders/pending/send-all         Send all due reminders
```

### Drug Routes (`/api/drugs`)
```
GET    /api/drugs/search              Search drugs by name
GET    /api/drugs/{emdex_id}          Get drug details
GET    /api/drugs/{name}/generics     Get generic alternatives
POST   /api/drugs/sync-emdex          Sync Emdex cache
GET    /api/drugs/prices/compare      Compare drug prices
```

### WhatsApp Routes (`/api/whatsapp`)
```
GET    /api/whatsapp/webhook          Webhook verification (GET)
POST   /api/whatsapp/webhook          Handle incoming messages (POST)
```

## 6. Background Tasks

### Reminder Scheduler
**File**: `app/tasks/reminders.py`

- Runs every 1 minute via APScheduler
- Queries SQLite for pending reminders
- Sends via WhatsApp Service
- Updates delivery status
- Syncs to Firebase for real-time delivery

**Status values:**
- `pending` - Created but not yet sent
- `sent` - Delivered via WhatsApp
- `taken` - User marked as taken
- `failed` - Delivery failed

## 7. Running the Server

### Development Mode
```bash
# Auto-reload on file changes
python -m uvicorn app.main:app --reload --port 8000
```

### Production Mode
```bash
# No auto-reload, optimized
python -m uvicorn app.main:app --port 8000 --workers 4
```

### Using Gunicorn (Recommended for Production)
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

## 8. Testing the API

### Using Swagger UI
Open: `http://localhost:8000/api/docs`

Interactive documentation where you can test all endpoints.

### Using cURL Examples

**Create a user:**
```bash
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+2348012345678",
    "name": "John Doe",
    "age": 35,
    "language_preference": "english"
  }'
```

**Upload prescription:**
```bash
curl -X POST "http://localhost:8000/api/prescriptions/USER_ID/upload" \
  -F "file=@prescription.jpg"
```

**Create medication:**
```bash
curl -X POST "http://localhost:8000/api/medications/USER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "drug_name": "Amoxicillin",
    "dosage": "500mg",
    "frequency": "3 times daily",
    "start_date": "2024-01-15T00:00:00",
    "reminder_times": ["09:00", "14:00", "18:00"]
  }'
```

**Schedule reminders:**
```bash
curl -X POST "http://localhost:8000/api/reminders/MED_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "reminder_times": ["09:00", "14:00", "18:00"]
  }'
```

**Get reminder stats:**
```bash
curl "http://localhost:8000/api/reminders/user/USER_ID/stats"
```

### Using Python Requests
```python
import requests

base_url = "http://localhost:8000/api"

# Create user
response = requests.post(f"{base_url}/users", json={
    "phone_number": "+2348012345678",
    "name": "John Doe"
})
user = response.json()

# Get medications
response = requests.get(f"{base_url}/medications/user/{user['id']}")
medications = response.json()
```

## 9. Deployment

### Deploy to Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create project
railway init

# Set environment variables
railway variables

# Deploy
railway deploy
```

### Deploy to Heroku
```bash
# Install Heroku CLI
# heroku login

# Create Procfile
echo "web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app" > Procfile

# Push to Heroku
git push heroku main
```

### Docker Deployment
```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build image
docker build -t medi-sync-backend .

# Run container
docker run -p 8000:8000 --env-file .env medi-sync-backend
```

## 10. Monitoring & Logs

### Application Logs
- Check console output for startup messages
- Background task execution logged every minute
- Error stack traces printed to console

### Database Logs
- SQLite queries logged with execution time
- Audit logs stored in `audit_logs` table

### Firebase Logs
- Check Firebase Console for real-time database activity
- Sync logs in `/sync_logs` path

## 11. Troubleshooting

### Common Issues

**Database Lock Error**
```
sqlite3.OperationalError: database is locked
```
Solution: Close other connections to database, restart server

**Firebase Connection Failed**
```
ServiceAccountCredentials failed
```
Solution: Check FIREBASE_SERVICE_ACCOUNT_KEY_PATH and file permissions

**WhatsApp Messages Not Sending**
```
Webhook token verification failed
```
Solution: Verify WHATSAPP_WEBHOOK_TOKEN matches Meta Business Console

**OCR Not Working**
```
Google Cloud Vision not initialized
```
Solution: Check GOOGLE_APPLICATION_CREDENTIALS and API is enabled

## 12. Development Workflow

### Adding a New API Endpoint

1. **Create model in** `app/models.py`
```python
class MyNewRequest(BaseModel):
    field: str
```

2. **Create route in** `app/routes/new_feature.py`
```python
from fastapi import APIRouter
router = APIRouter(prefix="/api/new", tags=["new"])

@router.post("/", response_model=SuccessResponse)
def my_endpoint(data: MyNewRequest):
    return {"success": True}
```

3. **Include in** `app/main.py`
```python
from .routes import new_feature
app.include_router(new_feature.router)
```

4. **Test in Swagger UI** at `/api/docs`

### Adding a New Service

1. **Create** `app/services/my_service.py`
2. **Implement class with methods**
3. **Create singleton getter function**
4. **Import and use in routes/other services**

## 13. Key Concepts

### Offline-First Architecture
- SQLite is primary database (always available)
- Firebase is secondary (for real-time sync when online)
- All operations work offline, sync when possible

### Reminder Scheduling
- Reminders created for entire medication duration
- Background job checks every minute
- WhatsApp delivery with status tracking
- Firebase push for real-time client notifications

### Data Sync Pattern
1. Update SQLite (source of truth)
2. Background job async syncs to Firebase
3. Client reads from Firebase for real-time updates
4. Fallback to SQLite if Firebase unavailable

### Multi-language Support
- User sets `language_preference` (english, yoruba, hausa, igbo)
- Messages template-based by language
- OCR works for image text in any language

## Success Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed from requirements.txt
- [ ] `.env` file created with all keys
- [ ] SQLite database initialized (`init_db.py` run)
- [ ] Firebase initialized (optional but recommended)
- [ ] Server starts without errors
- [ ] Swagger docs load at `/api/docs`
- [ ] Health check passes at `/health`
- [ ] Can create user via POST `/api/users`
- [ ] WhatsApp webhook ready (set callback URL in Meta console)
