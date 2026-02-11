"""API router for system status and data freshness."""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schemas import FreshnessResponse, FreshnessStatus
from app.core.database import get_db
from app.models.models import IngestionLog, IngestionStatus, Series

router = APIRouter()


@router.get("/status/freshness", response_model=FreshnessResponse)
def get_data_freshness(
    db: Session = Depends(get_db),
):
    """Get data freshness status for all sources.

    Returns:
        Freshness status for each data source
    """
    # Get all distinct sources
    sources = db.query(Series.source).distinct().all()
    source_names = [s[0] for s in sources]

    freshness_statuses: List[FreshnessStatus] = []

    for source in source_names:
        # Count series for this source
        series_count = db.query(Series).filter(Series.source == source).count()

        # Get last successful ingestion
        last_success = (
            db.query(IngestionLog)
            .filter(
                IngestionLog.source == source, IngestionLog.status == IngestionStatus.SUCCESS
            )
            .order_by(IngestionLog.completed_at.desc())
            .first()
        )

        # Get last failed ingestion
        last_failure = (
            db.query(IngestionLog)
            .filter(
                IngestionLog.source == source, IngestionLog.status == IngestionStatus.FAILURE
            )
            .order_by(IngestionLog.completed_at.desc())
            .first()
        )

        # Determine status
        status = "unknown"
        if last_success:
            # Check if data is fresh (within last 48 hours)
            if last_success.completed_at and (
                datetime.utcnow() - last_success.completed_at < timedelta(hours=48)
            ):
                status = "fresh"
            else:
                status = "stale"

        if last_failure and last_success:
            # If last failure is more recent than last success
            if (
                last_failure.completed_at
                and last_success.completed_at
                and last_failure.completed_at > last_success.completed_at
            ):
                status = "error"

        freshness_statuses.append(
            FreshnessStatus(
                source=source,
                series_count=series_count,
                last_successful_ingestion=last_success.completed_at if last_success else None,
                last_failed_ingestion=last_failure.completed_at if last_failure else None,
                status=status,
            )
        )

    # Determine overall status
    if all(s.status == "fresh" for s in freshness_statuses):
        overall_status = "healthy"
    elif any(s.status == "error" for s in freshness_statuses):
        overall_status = "degraded"
    elif any(s.status == "stale" for s in freshness_statuses):
        overall_status = "stale"
    else:
        overall_status = "unknown"

    return FreshnessResponse(sources=freshness_statuses, overall_status=overall_status)


@router.get("/status/health")
def health_check():
    """Basic health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "timestamp": datetime.utcnow()}
