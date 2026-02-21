"""
Medi-Sync AI Backend
Main FastAPI application entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from config import get_settings
from scripts.init_db import init_database
import os

# Initialize database on startup
db_path = os.getenv("DATABASE_PATH", "./data/medi_sync.db")
if not os.path.exists(db_path):
    init_database(db_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Medi-Sync AI API",
    description="Prescription management and medication reminder API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Setup CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from .routes import users, prescriptions, medications, reminders, drugs, whatsapp

# Include routers
app.include_router(users.router)
app.include_router(prescriptions.router)
app.include_router(medications.router)
app.include_router(reminders.router)
app.include_router(drugs.router)
app.include_router(whatsapp.router)

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "api_version": "1.0.0"
    }

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "Medi-Sync AI API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

# Error handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Starting Medi-Sync AI Backend")
    logger.info(f"Environment: {settings.environment}")
    
    # Start background tasks
    from .tasks.reminders import start_reminder_scheduler
    start_reminder_scheduler()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Medi-Sync AI Backend")
    
    # Stop background tasks
    from .tasks.reminders import stop_reminder_scheduler
    stop_reminder_scheduler()

if __name__ == "__main__":
    import uvicorn
    # The init_database call above handles the schema
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level="info"
    )
