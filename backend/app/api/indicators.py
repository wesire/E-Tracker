"""API router for indicators."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import Indicator
from app.core.database import get_db
from app.models.models import Indicator as IndicatorModel

router = APIRouter()


@router.get("/indicators", response_model=List[Indicator])
def list_indicators(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """List all available indicators.

    Args:
        category: Optional filter by indicator category
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of indicators
    """
    query = db.query(IndicatorModel)

    if category:
        query = query.filter(IndicatorModel.category == category)

    indicators = query.offset(skip).limit(limit).all()
    return indicators


@router.get("/indicators/{indicator_id}", response_model=Indicator)
def get_indicator(
    indicator_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific indicator by ID.

    Args:
        indicator_id: Indicator ID

    Returns:
        Indicator details
    """
    indicator = db.query(IndicatorModel).filter(IndicatorModel.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return indicator
