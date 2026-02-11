"""Data ingestion service with APScheduler."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.adapters import (
    BaseAdapter,
    FREDAdapter,
    OECDAdapter,
    ObservationData,
    WorldBankAdapter,
)
from app.core.config import get_settings
from app.models.models import (
    Country,
    Indicator,
    IngestionLog,
    IngestionStatus,
    Observation,
    Series,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class IngestionService:
    """Service for ingesting data from external sources."""

    def __init__(self):
        """Initialize ingestion service."""
        self.adapters: Dict[str, BaseAdapter] = {}
        self._init_adapters()

    def _init_adapters(self):
        """Initialize data source adapters."""
        # FRED adapter
        if settings.fred_api_key:
            self.adapters["FRED"] = FREDAdapter(
                {
                    "api_key": settings.fred_api_key,
                    "rate_limit_calls": settings.fred_rate_limit_calls,
                    "rate_limit_period": settings.fred_rate_limit_period,
                }
            )
        else:
            logger.warning("FRED API key not configured, FRED adapter disabled")

        # World Bank adapter
        self.adapters["WORLDBANK"] = WorldBankAdapter(
            {
                "rate_limit_calls": settings.world_bank_rate_limit_calls,
                "rate_limit_period": settings.world_bank_rate_limit_period,
            }
        )

        # OECD adapter
        self.adapters["OECD"] = OECDAdapter(
            {
                "rate_limit_calls": settings.oecd_rate_limit_calls,
                "rate_limit_period": settings.oecd_rate_limit_period,
            }
        )

    async def ingest_series(
        self,
        db: Session,
        series_id: int,
        lookback_days: int = 90,
    ) -> IngestionLog:
        """Ingest data for a specific series.

        Args:
            db: Database session
            series_id: Series ID to ingest
            lookback_days: Number of days to look back (default 90)

        Returns:
            IngestionLog record
        """
        started_at = datetime.utcnow()
        log = IngestionLog(
            source="",
            series_id=series_id,
            status=IngestionStatus.RUNNING,
            started_at=started_at,
        )

        try:
            # Get series from database
            series = db.query(Series).filter(Series.id == series_id).first()
            if not series:
                raise ValueError(f"Series {series_id} not found")

            log.source = series.source

            # Get adapter
            adapter = self.adapters.get(series.source)
            if not adapter:
                raise ValueError(f"Adapter for source {series.source} not available")

            # Determine date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)

            # Fetch observations
            observations = await adapter.fetch_observations(
                series.source_series_id, start_date, end_date
            )

            # Store observations
            records_stored = self._store_observations(db, series, observations)

            log.records_fetched = records_stored
            log.status = IngestionStatus.SUCCESS
            log.completed_at = datetime.utcnow()

            logger.info(
                f"Successfully ingested {records_stored} records for series {series_id} "
                f"from {series.source}"
            )

        except Exception as e:
            log.status = IngestionStatus.FAILURE
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            logger.error(f"Failed to ingest series {series_id}: {e}")

        # Save log
        db.add(log)
        db.commit()

        return log

    def _store_observations(
        self, db: Session, series: Series, observations: List[ObservationData]
    ) -> int:
        """Store observations in database.

        Args:
            db: Database session
            series: Series object
            observations: List of observations to store

        Returns:
            Number of records stored
        """
        records_stored = 0

        for obs_data in observations:
            # Check if observation already exists
            existing = (
                db.query(Observation)
                .filter(
                    Observation.series_id == series.id,
                    Observation.observation_date == obs_data.date,
                )
                .first()
            )

            if existing:
                # Update if value changed
                if existing.value != obs_data.value:
                    existing.value = obs_data.value
                    existing.vintage_date = obs_data.vintage_date
                    records_stored += 1
            else:
                # Create new observation
                observation = Observation(
                    series_id=series.id,
                    observation_date=obs_data.date,
                    value=obs_data.value,
                    vintage_date=obs_data.vintage_date,
                )
                db.add(observation)
                records_stored += 1

        db.commit()
        return records_stored

    async def ingest_all_series(self, db: Session, lookback_days: int = 90):
        """Ingest data for all active series.

        Args:
            db: Database session
            lookback_days: Number of days to look back
        """
        series_list = db.query(Series).all()

        logger.info(f"Starting ingestion for {len(series_list)} series")

        for series in series_list:
            try:
                await self.ingest_series(db, series.id, lookback_days)
            except Exception as e:
                logger.error(f"Failed to ingest series {series.id}: {e}")

        logger.info("Completed ingestion for all series")
