# Olive-AI Backend

Prescription management and medication reminder system built with FastAPI, SQLite, and Firebase. Provides OCR prescription scanning, drug matching, generic alternatives, and medication tracking.

## Features

- **🛡️ Secure Authentication**: Email and Password-based login with **bcrypt** hashing.
- **📄 Prescription OCR**: Scan and extract drugs from prescription images using Google Cloud Vision.
- **💊 Drug Database**: Match prescriptions against local knowledge base or Emdex API.
-  **🎁 Generic Alternatives**: Automated matching with generic versions to save costs.
- **🕒 Smart Reminders**: Schedule medication reminders with compliance tracking via WhatsApp.
- **☁️ Real-time Sync**: SQLite-based offline storage with Firebase real-time sync.
- **🌍 Multi-language**: Support for English, Yoruba, Hausa, and Igbo.

## Tech Stack the multi l

- **Framework**: FastAPI
- **Security**: Bcrypt (Password Hashing)
- **Database**: SQLite (Primary) + Firebase Realtime DB (Sync)
- **Deployment**: **Render (Free Tier)**
- **APIs**: Google Cloud Vision, WhatsApp Cloud API, Emdex (Fallback to Mock)
- **Server**: Uvicorn

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Firebase service account key (`firebase-credentials.json`)
- Google Cloud credentials (`lifecare.json`)

### Installation

1. **Clone repository**
```bash
git clone <repo-url>
cd Olive
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Initialize database**
```bash
python scripts/init_db.py
```

4. **Running the Server**
```bash
python -m uvicorn app.main:app --reload
```

**Interactive Docs**: `https://<your-url>.onrender.com/api/docs`

## 🌍 Deployment (Render.com)

This project is configured as a **Blueprint** for Render's Free Tier.

1.  Connect your GitHub repo to Render.
2.  Select **Blueprint** and point to `render.yaml`.
3.  Configure your **Secret Files** on Render:
    - `/etc/secrets/firebase-credentials.json`
    - `/etc/secrets/lifecare.json`
4.  The server will automatically boot and initialize the SQLite database in memory.

## 📡 API Endpoints (Core)

### Authentication
- `POST /api/users/` - Register new user
- `POST /api/users/login` - Login with Email/Password

### Prescriptions & Drugs
- `POST /api/prescriptions/{user_id}/upload` - Scan prescription image
- `GET /api/drugs/search` - Search local drug database
- `GET /api/drugs/{drug_name}/generics` - Get cheaper alternatives

### Reminders
- `POST /api/reminders/pending/send-all` - Trigger due reminders

## 📦 Project Structure

```
app/
├── routes/          # API Controllers
├── services/        # Business Logic (OCR, DB, WhatsApp)
├── models.py        # Pydantic Schemas
└── tasks/           # Background Schedulers
scripts/
└── init_db.py       # Database Schema Setup
render.yaml          # Infrastructure as Code
```

## License
MIT License - see LICENSE file for details
