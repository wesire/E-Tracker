"""API router for analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.recession_risk import RecessionRiskAssessor
from app.analytics.regime import RegimeClassifier
from app.api.schemas import RecessionRiskResponse, RegimeResponse
from app.core.database import get_db

router = APIRouter()


@router.get("/analytics/regime", response_model=RegimeResponse)
def get_regime_classification(
    db: Session = Depends(get_db),
    country_id: int = Query(..., description="Country ID (required)"),
):
    """Get economic regime classification for a country.

    Args:
        country_id: Country ID

    Returns:
        Regime classification (Expansion, Slowdown, Contraction, Recovery)
    """
    try:
        regime = RegimeClassifier.classify_regime(db, country_id)
        return regime
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to classify regime: {str(e)}"
        )


@router.get("/analytics/recession-risk", response_model=RecessionRiskResponse)
def get_recession_risk(
    db: Session = Depends(get_db),
    country_id: int = Query(..., description="Country ID (required)"),
):
    """Get recession risk assessment for a country.

    Args:
        country_id: Country ID

    Returns:
        Recession risk assessment with signals and score
    """
    try:
        risk = RecessionRiskAssessor.assess_recession_risk(db, country_id)
        return risk
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to assess recession risk: {str(e)}"
        )
