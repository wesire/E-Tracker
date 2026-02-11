"""API router for observations."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import Observation
from app.core.database import get_db
from app.models.models import Observation as ObservationModel

router = APIRouter()


@router.get("/observations", response_model=List[Observation])
def list_observations(
    db: Session = Depends(get_db),
    series_id: int = Query(..., description="Series ID (required)"),
    from_date: Optional[datetime] = Query(None, description="Start date (ISO 8601)"),
    to_date: Optional[datetime] = Query(None, description="End date (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
):
    """Get observations for a series with optional date range filtering.

    Args:
        series_id: Series ID (required)
        from_date: Optional start date filter
        to_date: Optional end date filter
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of observations
    """
    query = db.query(ObservationModel).filter(ObservationModel.series_id == series_id)

    if from_date:
        query = query.filter(ObservationModel.observation_date >= from_date)
    if to_date:
        query = query.filter(ObservationModel.observation_date <= to_date)

    observations = (
        query.order_by(ObservationModel.observation_date).offset(skip).limit(limit).all()
    )

    return observations
