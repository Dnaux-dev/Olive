# Medi-Sync AI Backend

Prescription management and medication reminder system built with FastAPI, SQLite, and Firebase. Provides OCR prescription scanning, drug matching, generic alternatives, WhatsApp reminders, and medication tracking.

## Features

- **Prescription OCR**: Scan and extract drugs from prescription images using Google Cloud Vision
- **Drug Database**: Match prescriptions against Emdex drug database with generic alternatives
- **Medication Management**: Track active medications with dosage and frequency
- **Smart Reminders**: Schedule WhatsApp medication reminders with compliance tracking
- **Offline Support**: SQLite-based offline storage with Firebase real-time sync
- **Multi-language**: Support for English, Yoruba, Hausa, and Igbo
- **Pill Verification**: Image-based pill identification and verification
- **Audit Trail**: Complete audit logging of all user actions

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: SQLite (primary) + Firebase Realtime DB (sync)
- **APIs**: Google Cloud Vision, Emdex Drug Database, WhatsApp Cloud API
- **Authentication**: Phone number based (OTP via WhatsApp)
- **Background Jobs**: APScheduler
- **Server**: Uvicorn

## Architecture

```
app/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration and environment variables
├── models.py              # Pydantic request/response models
├── routes/                # API endpoint definitions
│   ├── users.py           # User management endpoints
│   ├── prescriptions.py    # Prescription processing endpoints
│   ├── medications.py      # Medication management endpoints
│   ├── reminders.py        # Reminder scheduling endpoints
│   ├── drugs.py            # Drug database endpoints
│   └── whatsapp.py         # WhatsApp webhook and messaging
├── services/              # Business logic layer
│   ├── database_service.py # SQLite operations
│   ├── firebase_service.py # Firebase Realtime DB operations
│   ├── ocr_service.py      # Google Vision integration
│   ├── drug_service.py     # Emdex drug matching
│   ├── pill_service.py     # Pill image verification
│   ├── whatsapp_service.py # WhatsApp Cloud API integration
│   └── reminder_service.py # Reminder scheduling and delivery
└── tasks/                 # Background job definitions
    └── reminders.py       # Scheduled reminder sender

scripts/
├── init_db.py            # SQLite schema initialization
└── init_firebase.py      # Firebase Realtime DB setup
```

## Database Schema

### SQLite Tables
- `users` - User profiles with phone and language preferences
- `prescriptions` - Prescription documents with OCR results
- `prescription_drugs` - Junction table for prescription drugs
- `medications` - Active user medications with schedules
- `pills` - Pill image database for verification
- `drug_database` - Cached Emdex drug information
- `reminders` - Scheduled medication reminders
- `audit_logs` - User action audit trail

### Firebase Structure
```
/users/{userId}/
  ├── profile          # Synced user profile
  ├── medications      # Real-time medications
  ├── reminders        # Pending reminders
  └── lastSync         # Last sync timestamp
```

## Getting Started

### Prerequisites
- Python 3.9+
- Firebase project with service account key
- Google Cloud Vision API enabled
- WhatsApp Business Account with Cloud API access
- Emdex API key (optional, uses mocks for development)

### Installation

1. **Clone repository**
```bash
git clone <repo-url>
cd medi-sync-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Initialize database**
```bash
python scripts/init_db.py
```

6. **Initialize Firebase (if using)**
```bash
python scripts/init_firebase.py
```

### Running the Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

**Documentation**: http://localhost:8000/api/docs (Swagger UI)

## API Endpoints

### Users
- `POST /api/users` - Create user
- `GET /api/users/{user_id}` - Get user
- `GET /api/users/phone/{phone_number}` - Get user by phone
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user
- `POST /api/users/{user_id}/verify-phone` - Send verification code

### Prescriptions
- `POST /api/prescriptions/{user_id}` - Create prescription
- `POST /api/prescriptions/{user_id}/upload` - Upload and scan prescription
- `GET /api/prescriptions/{user_id}` - Get user prescriptions
- `GET /api/prescriptions/{prescription_id}` - Get prescription details
- `PUT /api/prescriptions/{prescription_id}` - Update prescription
- `DELETE /api/prescriptions/{prescription_id}` - Delete prescription

### Medications
- `POST /api/medications/{user_id}` - Create medication
- `GET /api/medications/{medication_id}` - Get medication
- `GET /api/medications/user/{user_id}` - Get user medications
- `PUT /api/medications/{medication_id}` - Update medication
- `DELETE /api/medications/{medication_id}` - Stop medication
- `POST /api/medications/{medication_id}/side-effect` - Report side effect

### Reminders
- `POST /api/reminders/{medication_id}` - Schedule reminders
- `GET /api/reminders/{reminder_id}` - Get reminder
- `GET /api/reminders/user/{user_id}` - Get user reminders
- `GET /api/reminders/user/{user_id}/stats` - Get reminder stats
- `POST /api/reminders/{reminder_id}/send` - Send reminder
- `POST /api/reminders/{reminder_id}/snooze` - Snooze reminder
- `POST /api/reminders/{reminder_id}/taken` - Mark as taken
- `POST /api/reminders/pending/send-all` - Send all due reminders

### Drugs
- `GET /api/drugs/search` - Search drugs
- `GET /api/drugs/{emdex_id}` - Get drug details
- `GET /api/drugs/{drug_name}/generics` - Get generic alternatives
- `POST /api/drugs/sync-emdex` - Sync Emdex database

### WhatsApp
- `GET /api/whatsapp/webhook` - Webhook verification
- `POST /api/whatsapp/webhook` - Handle incoming messages

## Environment Variables

```
# Firebase
FIREBASE_API_KEY=...
FIREBASE_DATABASE_URL=https://[PROJECT].firebaseio.com
FIREBASE_PROJECT_ID=...
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=./firebase-credentials.json

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./google-credentials.json
GCP_PROJECT_ID=...

# Emdex API
EMDEX_API_KEY=...
EMDEX_API_URL=https://api.emdex.ng

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_WEBHOOK_TOKEN=...

# Database
DATABASE_PATH=./data/medi_sync.db

# Application
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key
```

## Background Tasks

### Reminder Scheduler
Runs every minute to check for due reminders and send via WhatsApp:
- Queries SQLite for pending reminders
- Sends WhatsApp messages
- Updates delivery status
- Syncs to Firebase for real-time delivery

## Testing

### Mock Data
All external APIs have mock implementations for development:
- Google Vision OCR returns mock prescription text
- Emdex API returns mock drug data
- WhatsApp returns mock message IDs

### Unit Tests
```bash
pytest app/tests -v
```

## Deployment

### Local Development
```bash
python -m uvicorn app.main:app --reload
```

### Production with Railway
```bash
pip freeze > requirements.txt
# Connect Railway to GitHub, select this repo
# Railway auto-detects Python and starts the server
```

### Production with Docker
```bash
docker build -t medi-sync-backend .
docker run -p 8000:8000 --env-file .env medi-sync-backend
```

## Key Implementation Details

### Offline-First Architecture
- SQLite is the primary database and source of truth
- All data persists locally even without internet
- Firebase syncs user data when online for real-time features
- Reminders can work offline with scheduled checks every minute

### Dual-Write Pattern
- User updates write to SQLite first
- Background job async syncs to Firebase
- Ensures data consistency and fallback capability

### WhatsApp Integration
- Phone number-based authentication (no passwords for MVP)
- Users can upload prescriptions via WhatsApp images
- Bot responds to commands: /medications, /reminders, /stats
- Automatic reminders sent via WhatsApp at scheduled times

### Drug Matching
- First checks local SQLite cache
- Falls back to Emdex API if not cached
- Returns generic alternatives with price comparisons
- NAFDAC verification status included

## Troubleshooting

### Database Issues
```bash
# Recreate database
rm ./data/medi_sync.db
python scripts/init_db.py
```

### Firebase Connection
- Ensure serviceAccountKey.json is in correct location
- Check FIREBASE_DATABASE_URL format
- Verify Firebase Realtime DB is enabled in Console

### WhatsApp Messages Not Sending
- Check WHATSAPP_ACCESS_TOKEN is valid
- Verify WHATSAPP_PHONE_NUMBER_ID matches your number
- Check webhook token verification in console logs

## Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and support, please open a GitHub issue or contact the development team.
