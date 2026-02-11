"""API router for series."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import Series
from app.core.database import get_db
from app.models.models import Series as SeriesModel

router = APIRouter()


@router.get("/series", response_model=List[Series])
def list_series(
    db: Session = Depends(get_db),
    country_id: Optional[int] = Query(None, description="Filter by country ID"),
    indicator_id: Optional[int] = Query(None, description="Filter by indicator ID"),
    source: Optional[str] = Query(None, description="Filter by data source"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """List series with optional filters.

    Args:
        country_id: Optional filter by country ID
        indicator_id: Optional filter by indicator ID
        source: Optional filter by data source
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of series
    """
    query = db.query(SeriesModel)

    if country_id:
        query = query.filter(SeriesModel.country_id == country_id)
    if indicator_id:
        query = query.filter(SeriesModel.indicator_id == indicator_id)
    if source:
        query = query.filter(SeriesModel.source == source)

    series = query.offset(skip).limit(limit).all()
    return series


@router.get("/series/{series_id}", response_model=Series)
def get_series(
    series_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific series by ID.

    Args:
        series_id: Series ID

    Returns:
        Series details
    """
    series = db.query(SeriesModel).filter(SeriesModel.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series
