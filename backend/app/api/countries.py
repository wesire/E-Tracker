"""API router for countries."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import Country
from app.core.database import get_db
from app.models.models import Country as CountryModel

router = APIRouter()


@router.get("/countries", response_model=List[Country])
def list_countries(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """List all available countries.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of countries
    """
    countries = db.query(CountryModel).offset(skip).limit(limit).all()
    return countries


@router.get("/countries/{country_id}", response_model=Country)
def get_country(
    country_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific country by ID.

    Args:
        country_id: Country ID

    Returns:
        Country details
    """
    country = db.query(CountryModel).filter(CountryModel.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country
