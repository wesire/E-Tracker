"""SQLAlchemy models for the Economy Tracker database schema."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class Country(Base):
    """Countries/regions for which economic data is tracked."""

    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    iso_alpha2 = Column(String(2), unique=True, index=True)
    iso_alpha3 = Column(String(3), unique=True, index=True)
    region = Column(String(100))

    # Relationships
    series = relationship("Series", back_populates="country")


class IndicatorCategory(str, enum.Enum):
    """Categories of economic indicators."""

    GDP = "gdp"
    INFLATION = "inflation"
    EMPLOYMENT = "employment"
    INTEREST_RATE = "interest_rate"
    TRADE = "trade"
    OTHER = "other"


class Indicator(Base):
    """Economic indicators that are tracked."""

    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text)
    category = Column(Enum(IndicatorCategory), nullable=False, index=True)
    unit = Column(String(50))  # e.g., "percent", "index", "billions"
    default_frequency = Column(String(20))  # e.g., "monthly", "quarterly", "annual"

    # Relationships
    series = relationship("Series", back_populates="indicator")


class Series(Base):
    """Time series representing a specific indicator for a specific country from a specific source."""

    __tablename__ = "series"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)  # e.g., "FRED", "World Bank", "OECD"
    source_series_id = Column(String(200), nullable=False)  # ID used by the source
    frequency = Column(String(20))  # "monthly", "quarterly", "annual"
    seasonal_adjustment = Column(String(50))  # e.g., "seasonally_adjusted", "not_adjusted"
    unit_override = Column(String(50))  # Override unit from indicator if needed
    metadata_json = Column(JSON)  # Additional metadata from source

    # Relationships
    indicator = relationship("Indicator", back_populates="series")
    country = relationship("Country", back_populates="series")
    observations = relationship("Observation", back_populates="series")
    ingestion_logs = relationship("IngestionLog", back_populates="series")
    watchlists = relationship("UserWatchlist", back_populates="series")
    alerts = relationship("Alert", back_populates="series")

    __table_args__ = (
        Index("idx_series_source_source_id", "source", "source_series_id"),
        Index("idx_series_indicator_country", "indicator_id", "country_id"),
    )


class Observation(Base):
    """Individual data points in a time series."""

    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("series.id"), nullable=False, index=True)
    observation_date = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    vintage_date = Column(DateTime)  # When this data point was published/revised
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    series = relationship("Series", back_populates="observations")

    __table_args__ = (
        Index("idx_observations_series_date", "series_id", "observation_date"),
        Index("idx_observations_date", "observation_date"),
    )


class IngestionStatus(str, enum.Enum):
    """Status of data ingestion."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    RUNNING = "running"


class IngestionLog(Base):
    """Logs of data ingestion runs."""

    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("series.id"), index=True)
    status = Column(Enum(IngestionStatus), nullable=False, index=True)
    records_fetched = Column(Integer)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime)

    # Relationships
    series = relationship("Series", back_populates="ingestion_logs")


class UserWatchlist(Base):
    """User watchlists for tracking specific series."""

    __tablename__ = "user_watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_session_id = Column(String(100), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("series.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    series = relationship("Series", back_populates="watchlists")

    __table_args__ = (Index("idx_watchlist_user_series", "user_session_id", "series_id"),)


class AlertConditionType(str, enum.Enum):
    """Types of alert conditions."""

    ABOVE = "above"
    BELOW = "below"
    CHANGE = "change"


class Alert(Base):
    """User-defined alerts for series."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_session_id = Column(String(100), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("series.id"), nullable=False, index=True)
    condition_type = Column(Enum(AlertConditionType), nullable=False)
    threshold_value = Column(Float, nullable=False)
    lookback_months = Column(Integer)  # For "change" condition
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    series = relationship("Series", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert")


class Notification(Base):
    """Notifications generated when alerts are triggered."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    alert = relationship("Alert", back_populates="notifications")
