"""API router for insights."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import CountryInsightsResponse, InsightResponse
from app.core.database import get_db
from app.insights.generator import InsightGenerator

router = APIRouter()


@router.get("/insights", response_model=CountryInsightsResponse)
def get_country_insights(
    db: Session = Depends(get_db),
    country_id: int = Query(..., description="Country ID (required)"),
):
    """Get generated insights for a country.

    Args:
        country_id: Country ID

    Returns:
        Comprehensive insights including regime, recession risk, and indicator narratives
    """
    try:
        insights = InsightGenerator.generate_country_insights(db, country_id)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.get("/insights/series/{series_id}", response_model=InsightResponse)
def get_series_insight(
    series_id: int,
    db: Session = Depends(get_db),
):
    """Get generated insight for a specific series.

    Args:
        series_id: Series ID

    Returns:
        Narrative insight for the series
    """
    try:
        insight = InsightGenerator.generate_indicator_insight(db, series_id)
        if "error" in insight:
            raise HTTPException(status_code=404, detail=insight["error"])
        return insight
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insight: {str(e)}")
