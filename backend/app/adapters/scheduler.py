"""Background scheduler for data ingestion."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.adapters.ingestion import IngestionService
from app.core.config import get_settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()


class SchedulerService:
    """Service for scheduling background jobs."""

    def __init__(self):
        """Initialize scheduler service."""
        self.scheduler = AsyncIOScheduler()
        self.ingestion_service = IngestionService()

    async def ingest_data_job(self):
        """Background job to ingest data from all sources."""
        logger.info("Starting scheduled data ingestion")
        db: Session = SessionLocal()
        try:
            await self.ingestion_service.ingest_all_series(db, lookback_days=90)
        except Exception as e:
            logger.error(f"Scheduled ingestion failed: {e}")
        finally:
            db.close()

    def start(self):
        """Start the scheduler."""
        # Parse cron schedule from settings
        # Default: "0 6 * * *" (daily at 6 AM)
        cron_parts = settings.ingestion_schedule.split()
        if len(cron_parts) == 5:
            minute, hour, day, month, day_of_week = cron_parts
            
            self.scheduler.add_job(
                self.ingest_data_job,
                "cron",
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                id="data_ingestion",
            )
            logger.info(f"Scheduled data ingestion with cron: {settings.ingestion_schedule}")
        else:
            logger.warning(
                f"Invalid cron schedule: {settings.ingestion_schedule}, using default (daily at 6 AM)"
            )
            self.scheduler.add_job(
                self.ingest_data_job,
                "cron",
                hour=6,
                minute=0,
                id="data_ingestion",
            )

        self.scheduler.start()
        logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")


# Global scheduler instance
scheduler_service = SchedulerService()
