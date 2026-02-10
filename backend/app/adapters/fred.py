"""FRED (Federal Reserve Economic Data) adapter."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from dateutil import parser

from app.adapters.base import (
    AdapterError,
    AuthenticationError,
    BaseAdapter,
    DataNotFoundError,
    ObservationData,
    RateLimitError,
    SeriesMetadata,
)
from app.adapters.rate_limiter import RateLimiter
from app.adapters.retry import with_retry

logger = logging.getLogger(__name__)


class FREDAdapter(BaseAdapter):
    """Adapter for Federal Reserve Economic Data (FRED) API."""

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, config: Dict[str, Any]):
        """Initialize FRED adapter.

        Args:
            config: Configuration dictionary with 'api_key', 'rate_limit_calls', 'rate_limit_period'
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        if not self.api_key:
            logger.warning("FRED API key not configured")

        # Setup rate limiter
        self.rate_limiter = RateLimiter(
            max_calls=config.get("rate_limit_calls", 120),
            period=config.get("rate_limit_period", 60),
        )

    @with_retry(max_attempts=3, backoff_factor=2, initial_delay=1.0)
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to FRED API with rate limiting and retry.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response

        Raises:
            AdapterError: If request fails
        """
        await self.rate_limiter.acquire()

        params["api_key"] = self.api_key
        params["file_type"] = "json"

        url = f"{self.BASE_URL}/{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=30.0)

                if response.status_code == 400:
                    error_data = response.json()
                    error_message = error_data.get("error_message", "Bad request")
                    if "API key" in error_message:
                        raise AuthenticationError(f"FRED API authentication failed: {error_message}")
                    raise AdapterError(f"FRED API error: {error_message}")

                if response.status_code == 404:
                    raise DataNotFoundError("Series not found in FRED")

                if response.status_code == 429:
                    raise RateLimitError("FRED API rate limit exceeded")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                raise AdapterError(f"FRED API request failed: {e}")

    async def fetch_series_metadata(self, series_id: str) -> SeriesMetadata:
        """Fetch metadata for a FRED series.

        Args:
            series_id: FRED series ID (e.g., 'CPIAUCSL', 'UNRATE')

        Returns:
            SeriesMetadata object
        """
        data = await self._make_request("series", {"series_id": series_id})

        series_data = data.get("seriess", [])[0] if data.get("seriess") else {}

        return SeriesMetadata(
            source_series_id=series_id,
            title=series_data.get("title", ""),
            frequency=series_data.get("frequency", ""),
            units=series_data.get("units", ""),
            seasonal_adjustment=series_data.get("seasonal_adjustment", ""),
            last_updated=parser.parse(series_data["last_updated"])
            if series_data.get("last_updated")
            else None,
            notes=series_data.get("notes"),
            extra={
                "frequency_short": series_data.get("frequency_short"),
                "units_short": series_data.get("units_short"),
                "popularity": series_data.get("popularity"),
            },
        )

    async def fetch_observations(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ObservationData]:
        """Fetch observations for a FRED series.

        Args:
            series_id: FRED series ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of ObservationData objects
        """
        params = {"series_id": series_id}

        if start_date:
            params["observation_start"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["observation_end"] = end_date.strftime("%Y-%m-%d")

        data = await self._make_request("series/observations", params)

        observations = []
        for obs in data.get("observations", []):
            # Skip missing values
            if obs.get("value") == ".":
                continue

            try:
                observations.append(
                    ObservationData(
                        date=parser.parse(obs["date"]),
                        value=float(obs["value"]),
                        vintage_date=parser.parse(obs.get("realtime_end"))
                        if obs.get("realtime_end")
                        else None,
                    )
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid observation for {series_id}: {e}")

        return observations

    async def test_connection(self) -> bool:
        """Test connection to FRED API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to fetch a well-known series
            await self.fetch_series_metadata("CPIAUCSL")
            return True
        except Exception as e:
            logger.error(f"FRED connection test failed: {e}")
            return False
