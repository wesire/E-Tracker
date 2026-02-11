"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Country schemas
class CountryBase(BaseModel):
    name: str
    iso_alpha2: Optional[str] = None
    iso_alpha3: Optional[str] = None
    region: Optional[str] = None


class CountryCreate(CountryBase):
    pass


class Country(CountryBase):
    id: int

    class Config:
        from_attributes = True


# Indicator schemas
class IndicatorBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    unit: Optional[str] = None
    default_frequency: Optional[str] = None


class IndicatorCreate(IndicatorBase):
    pass


class Indicator(IndicatorBase):
    id: int

    class Config:
        from_attributes = True


# Series schemas
class SeriesBase(BaseModel):
    indicator_id: int
    country_id: int
    source: str
    source_series_id: str
    frequency: Optional[str] = None
    seasonal_adjustment: Optional[str] = None
    unit_override: Optional[str] = None
    metadata_json: Optional[dict] = None


class SeriesCreate(SeriesBase):
    pass


class Series(SeriesBase):
    id: int

    class Config:
        from_attributes = True


# Observation schemas
class ObservationBase(BaseModel):
    observation_date: datetime
    value: float
    vintage_date: Optional[datetime] = None


class Observation(ObservationBase):
    id: int
    series_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Watchlist schemas
class WatchlistCreate(BaseModel):
    user_session_id: str
    series_id: int


class Watchlist(BaseModel):
    id: int
    user_session_id: str
    series_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Alert schemas
class AlertCreate(BaseModel):
    user_session_id: str
    series_id: int
    condition_type: str
    threshold_value: float
    lookback_months: Optional[int] = None


class AlertUpdate(BaseModel):
    is_active: Optional[bool] = None
    threshold_value: Optional[float] = None


class Alert(BaseModel):
    id: int
    user_session_id: str
    series_id: int
    condition_type: str
    threshold_value: float
    lookback_months: Optional[int]
    is_active: bool
    triggered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# Notification schemas
class Notification(BaseModel):
    id: int
    alert_id: int
    message: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Pagination schemas
class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total_pages: int


# Insights schemas
class InsightResponse(BaseModel):
    series_id: int
    indicator_name: str
    country_name: str
    latest_date: datetime
    what_changed: str
    why_it_matters: str
    risk_signals: List[str]
    metrics: dict


class CountryInsightsResponse(BaseModel):
    country_id: int
    regime: dict
    recession_risk: dict
    indicator_insights: List[InsightResponse]
    generated_at: datetime


# Analytics schemas
class RegimeResponse(BaseModel):
    regime: str
    confidence: float
    signals: List[str]
    gdp_growth_yoy: Optional[float]
    gdp_qoq_annualized: Optional[float]
    unemployment_rate: Optional[float]
    unemployment_change_yoy: Optional[float]


class RecessionRiskResponse(BaseModel):
    risk_level: str
    risk_score: float
    risk_signals: List[dict]
    metrics: dict


# Freshness schemas
class FreshnessStatus(BaseModel):
    source: str
    series_count: int
    last_successful_ingestion: Optional[datetime]
    last_failed_ingestion: Optional[datetime]
    status: str


class FreshnessResponse(BaseModel):
    sources: List[FreshnessStatus]
    overall_status: str
