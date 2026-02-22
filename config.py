from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    """Application configuration from environment variables"""
    
    # Firebase
    firebase_api_key: str = ""
    firebase_auth_domain: str = ""
    firebase_database_url: str = ""
    firebase_project_id: str = ""
    firebase_storage_bucket: str = ""
    firebase_messaging_sender_id: str = ""
    firebase_app_id: str = ""
    firebase_service_account_key_path: str = "./firebase-credentials.json"
    
    # Google Cloud
    google_application_credentials: str = "./google-credentials.json"
    gcp_project_id: str = ""
    
    # Emdex API
    emdex_api_key: str = ""
    emdex_api_url: str = "https://api.emdex.ng"
    
    # WhatsApp
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_webhook_token: str = ""
    whatsapp_business_account_id: str = ""
    
    # Email
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    resend_from_email: str = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@medisync.ai"
    
    # Database
    database_path: str = "./data/medi_sync.db"
    
    # Application
    environment: str = "development"
    api_url: str = os.getenv("API_URL", "http://localhost:8000")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "your_secret_key_change_in_production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # Default 24 hours
    
    # AI APIs
    google_ai_api_key: Optional[str] = os.getenv("GOOGLE_AI_API_KEY")
    yarngpt_api_key: Optional[str] = os.getenv("YARNGPT_API_KEY")
    
    # CORS
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Deployment
    railway_api_token: str = ""
    
    # Cloud Credentials (for JSON content)
    google_credentials_json: Optional[str] = None
    firebase_credentials_json: Optional[str] = None

    def setup_google_credentials(self):
        """Write Google JSON credentials to file if provided via env"""
        if self.google_credentials_json:
            with open(self.google_application_credentials, "w") as f:
                f.write(self.google_credentials_json)

    def setup_firebase_credentials(self):
        """Write Firebase JSON credentials to file if provided via env"""
        if self.firebase_credentials_json:
            with open(self.firebase_service_account_key_path, "w") as f:
                f.write(self.firebase_credentials_json)
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance and setup cloud credentials"""
    settings = Settings()
    settings.setup_google_credentials()
    settings.setup_firebase_credentials()
    return settings
