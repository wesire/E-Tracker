"""Base adapter interface for data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ObservationData:
    """Data point from a data source."""

    date: datetime
    value: float
    vintage_date: Optional[datetime] = None


@dataclass
class SeriesMetadata:
    """Metadata about a time series."""

    source_series_id: str
    title: str
    frequency: str
    units: str
    seasonal_adjustment: Optional[str] = None
    last_updated: Optional[datetime] = None
    notes: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class BaseAdapter(ABC):
    """Base class for data source adapters."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize adapter with configuration."""
        self.config = config
        self.source_name = self.__class__.__name__.replace("Adapter", "").upper()

    @abstractmethod
    async def fetch_series_metadata(self, series_id: str) -> SeriesMetadata:
        """Fetch metadata for a series.

        Args:
            series_id: Source-specific series identifier

        Returns:
            SeriesMetadata object

        Raises:
            AdapterError: If fetch fails
        """
        pass

    @abstractmethod
    async def fetch_observations(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ObservationData]:
        """Fetch observations for a series.

        Args:
            series_id: Source-specific series identifier
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of ObservationData objects

        Raises:
            AdapterError: If fetch fails
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the data source.

        Returns:
            True if connection successful, False otherwise
        """
        pass


class AdapterError(Exception):
    """Base exception for adapter errors."""

    pass


class RateLimitError(AdapterError):
    """Raised when rate limit is exceeded."""

    pass


class AuthenticationError(AdapterError):
    """Raised when authentication fails."""

    pass


class DataNotFoundError(AdapterError):
    """Raised when requested data is not found."""

    pass
