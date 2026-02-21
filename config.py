from pydantic_settings import BaseSettings
from functools import lru_cache
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
    
    # Database
    database_path: str = "./data/medi_sync.db"
    
    # Application
    environment: str = "development"
    api_url: str = "http://localhost:8000"
    debug: bool = True
    secret_key: str = "your_secret_key_change_in_production"
    
    # Deployment
    railway_api_token: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
