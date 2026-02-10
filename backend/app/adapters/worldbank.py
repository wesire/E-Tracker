"""World Bank API adapter."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from dateutil import parser

from app.adapters.base import (
    AdapterError,
    BaseAdapter,
    DataNotFoundError,
    ObservationData,
    RateLimitError,
    SeriesMetadata,
)
from app.adapters.rate_limiter import RateLimiter
from app.adapters.retry import with_retry

logger = logging.getLogger(__name__)


class WorldBankAdapter(BaseAdapter):
    """Adapter for World Bank API."""

    BASE_URL = "https://api.worldbank.org/v2"

    def __init__(self, config: Dict[str, Any]):
        """Initialize World Bank adapter.

        Args:
            config: Configuration dictionary with 'rate_limit_calls', 'rate_limit_period'
        """
        super().__init__(config)

        # Setup rate limiter
        self.rate_limiter = RateLimiter(
            max_calls=config.get("rate_limit_calls", 100),
            period=config.get("rate_limit_period", 60),
        )

    @with_retry(max_attempts=3, backoff_factor=2, initial_delay=1.0)
    async def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """Make HTTP request to World Bank API with rate limiting and retry.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            AdapterError: If request fails
        """
        await self.rate_limiter.acquire()

        default_params = {"format": "json", "per_page": 1000}
        if params:
            default_params.update(params)

        url = f"{self.BASE_URL}/{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=default_params, timeout=30.0)

                if response.status_code == 404:
                    raise DataNotFoundError("Data not found in World Bank")

                if response.status_code == 429:
                    raise RateLimitError("World Bank API rate limit exceeded")

                response.raise_for_status()
                data = response.json()

                # World Bank returns [metadata, data]
                if isinstance(data, list) and len(data) > 1:
                    return data[1] if data[1] else []
                return []

            except httpx.HTTPError as e:
                raise AdapterError(f"World Bank API request failed: {e}")

    async def fetch_series_metadata(self, series_id: str) -> SeriesMetadata:
        """Fetch metadata for a World Bank indicator.

        Args:
            series_id: World Bank indicator code (e.g., 'NY.GDP.MKTP.KD.ZG')

        Returns:
            SeriesMetadata object
        """
        # Extract country and indicator from series_id (format: country/indicator)
        parts = series_id.split("/")
        if len(parts) == 2:
            country_code, indicator_code = parts
        else:
            indicator_code = series_id
            country_code = "WLD"  # Default to World

        data = await self._make_request(f"indicator/{indicator_code}")

        if not data:
            raise DataNotFoundError(f"Indicator {indicator_code} not found")

        indicator_data = data[0]

        return SeriesMetadata(
            source_series_id=series_id,
            title=indicator_data.get("name", ""),
            frequency="annual",  # World Bank data is typically annual
            units=indicator_data.get("unit", ""),
            seasonal_adjustment=None,
            notes=indicator_data.get("sourceNote"),
            extra={
                "source_organization": indicator_data.get("sourceOrganization"),
                "topics": indicator_data.get("topics", []),
            },
        )

    async def fetch_observations(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ObservationData]:
        """Fetch observations for a World Bank indicator.

        Args:
            series_id: World Bank series ID (format: 'country/indicator' or just 'indicator')
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of ObservationData objects
        """
        # Extract country and indicator from series_id
        parts = series_id.split("/")
        if len(parts) == 2:
            country_code, indicator_code = parts
        else:
            indicator_code = series_id
            country_code = "WLD"  # Default to World

        # Build date range parameter
        date_range = ""
        if start_date and end_date:
            date_range = f"{start_date.year}:{end_date.year}"
        elif start_date:
            date_range = f"{start_date.year}:{datetime.now().year}"

        params = {}
        if date_range:
            params["date"] = date_range

        # Fetch data
        endpoint = f"country/{country_code}/indicator/{indicator_code}"
        data = await self._make_request(endpoint, params)

        observations = []
        for item in data:
            if item.get("value") is None:
                continue

            try:
                # World Bank uses year for date
                year = int(item["date"])
                observations.append(
                    ObservationData(
                        date=datetime(year, 1, 1),
                        value=float(item["value"]),
                        vintage_date=None,
                    )
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid observation for {series_id}: {e}")

        # Sort by date (World Bank returns newest first)
        observations.sort(key=lambda x: x.date)

        return observations

    async def test_connection(self) -> bool:
        """Test connection to World Bank API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to fetch a well-known indicator
            await self._make_request("indicator/NY.GDP.MKTP.CD")
            return True
        except Exception as e:
            logger.error(f"World Bank connection test failed: {e}")
            return False
