"""Adapters package."""

from app.adapters.base import (
    AdapterError,
    AuthenticationError,
    BaseAdapter,
    DataNotFoundError,
    ObservationData,
    RateLimitError,
    SeriesMetadata,
)
from app.adapters.fred import FREDAdapter
from app.adapters.oecd import OECDAdapter
from app.adapters.worldbank import WorldBankAdapter

__all__ = [
    "AdapterError",
    "AuthenticationError",
    "BaseAdapter",
    "DataNotFoundError",
    "FREDAdapter",
    "OECDAdapter",
    "ObservationData",
    "RateLimitError",
    "SeriesMetadata",
    "WorldBankAdapter",
]
