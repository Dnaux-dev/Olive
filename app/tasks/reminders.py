"""
Background Tasks for Reminders
Handles scheduled reminder delivery
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def send_due_reminders():
    """Job function to send all due reminders"""
    try:
        from ..services.reminder_service import get_reminder_service
        reminder_service = get_reminder_service()
        
        logger.info(f"[{datetime.now().isoformat()}] Checking for due reminders...")
        
        results = reminder_service.send_all_due_reminders()
        
        if results['sent'] > 0 or results['failed'] > 0:
            logger.info(f"Reminders sent: {results['sent']}, failed: {results['failed']}")
        
        if results['errors']:
            logger.warning(f"Reminder errors: {results['errors']}")
    
    except Exception as e:
        logger.error(f"Error in reminder scheduler: {e}", exc_info=True)

def start_reminder_scheduler():
    """Start the background reminder scheduler"""
    global scheduler
    
    try:
        if scheduler is None:
            scheduler = BackgroundScheduler()
            
            # Add job to check for due reminders every minute
            scheduler.add_job(
                send_due_reminders,
                trigger=IntervalTrigger(minutes=1),
                id='send_due_reminders',
                name='Send Due Reminders',
                replace_existing=True,
                max_instances=1  # Only one instance at a time
            )
            
            scheduler.start()
            logger.info("Reminder scheduler started - checking every minute")
    
    except Exception as e:
        logger.error(f"Failed to start reminder scheduler: {e}")

def stop_reminder_scheduler():
    """Stop the background reminder scheduler"""
    global scheduler
    
    try:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Reminder scheduler stopped")
    
    except Exception as e:
        logger.error(f"Error stopping reminder scheduler: {e}")

def get_scheduler_status():
    """Get current scheduler status"""
    global scheduler
    
    if scheduler is None:
        return {
            'running': False,
            'jobs': []
        }
    
    return {
        'running': scheduler.running,
        'jobs': [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }
