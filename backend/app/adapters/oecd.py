"""OECD SDMX/JSON adapter."""

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


class OECDAdapter(BaseAdapter):
    """Adapter for OECD SDMX/JSON API."""

    BASE_URL = "https://sdmx.oecd.org/public/rest/data"

    def __init__(self, config: Dict[str, Any]):
        """Initialize OECD adapter.

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
        self, dataset: str, filters: str = "all", params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to OECD API with rate limiting and retry.

        Args:
            dataset: OECD dataset identifier
            filters: Filter string (e.g., 'USA.CPI')
            params: Query parameters

        Returns:
            JSON response

        Raises:
            AdapterError: If request fails
        """
        await self.rate_limiter.acquire()

        default_params = {"format": "jsondata"}
        if params:
            default_params.update(params)

        url = f"{self.BASE_URL}/{dataset}/{filters}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=default_params, timeout=30.0)

                if response.status_code == 404:
                    raise DataNotFoundError("Data not found in OECD")

                if response.status_code == 429:
                    raise RateLimitError("OECD API rate limit exceeded")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                raise AdapterError(f"OECD API request failed: {e}")

    async def fetch_series_metadata(self, series_id: str) -> SeriesMetadata:
        """Fetch metadata for an OECD series.

        Args:
            series_id: OECD series ID (format: 'dataset/filter', e.g., 'MEI/USA.CPALTT01.IXOB.M')

        Returns:
            SeriesMetadata object
        """
        # Parse series_id
        parts = series_id.split("/")
        if len(parts) != 2:
            raise AdapterError(f"Invalid OECD series ID format: {series_id}")

        dataset, filters = parts

        try:
            data = await self._make_request(dataset, filters, {"detail": "dataonly"})

            # Extract metadata from structure
            structure = data.get("structure", {})
            dimensions = structure.get("dimensions", {}).get("observation", [])

            # Try to get series info
            dataset_info = data.get("dataSets", [{}])[0]
            series_info = dataset_info.get("series", {})

            return SeriesMetadata(
                source_series_id=series_id,
                title=f"OECD {dataset} - {filters}",
                frequency="monthly",  # Default, may vary
                units="index",  # Default, may vary
                seasonal_adjustment=None,
                extra={
                    "dataset": dataset,
                    "filters": filters,
                    "dimensions": [dim.get("name") for dim in dimensions],
                },
            )
        except Exception as e:
            logger.warning(f"Could not fetch full metadata for {series_id}: {e}")
            # Return minimal metadata
            return SeriesMetadata(
                source_series_id=series_id,
                title=f"OECD {series_id}",
                frequency="monthly",
                units="index",
            )

    async def fetch_observations(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ObservationData]:
        """Fetch observations for an OECD series.

        Args:
            series_id: OECD series ID (format: 'dataset/filter')
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of ObservationData objects
        """
        # Parse series_id
        parts = series_id.split("/")
        if len(parts) != 2:
            raise AdapterError(f"Invalid OECD series ID format: {series_id}")

        dataset, filters = parts

        params = {"detail": "dataonly"}
        if start_date:
            params["startPeriod"] = start_date.strftime("%Y-%m")
        if end_date:
            params["endPeriod"] = end_date.strftime("%Y-%m")

        data = await self._make_request(dataset, filters, params)

        observations = []

        try:
            # Navigate SDMX-JSON structure
            dataset_info = data.get("dataSets", [{}])[0]
            series_data = dataset_info.get("series", {})

            # OECD uses indexed structure - try first series
            for series_key, series_info in series_data.items():
                obs_data = series_info.get("observations", {})

                # Get time dimension
                structure = data.get("structure", {})
                time_dimension = structure.get("dimensions", {}).get("observation", [])
                time_values = []
                for dim in time_dimension:
                    if dim.get("role") == "time" or dim.get("id") == "TIME_PERIOD":
                        time_values = [v.get("id") for v in dim.get("values", [])]
                        break

                # Parse observations
                for obs_index, obs_value_list in obs_data.items():
                    if not obs_value_list:
                        continue

                    obs_index_int = int(obs_index)
                    if obs_index_int >= len(time_values):
                        continue

                    time_str = time_values[obs_index_int]
                    value = obs_value_list[0]

                    if value is None:
                        continue

                    try:
                        # Parse time period (e.g., "2024-01", "2024-Q1", "2024")
                        if "-Q" in time_str:  # Quarterly
                            year, quarter = time_str.split("-Q")
                            month = (int(quarter) - 1) * 3 + 1
                            date_obj = datetime(int(year), month, 1)
                        elif "-" in time_str:  # Monthly
                            date_obj = parser.parse(time_str + "-01")
                        else:  # Annual
                            date_obj = datetime(int(time_str), 1, 1)

                        observations.append(
                            ObservationData(
                                date=date_obj,
                                value=float(value),
                                vintage_date=None,
                            )
                        )
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid observation for {series_id}: {e}")

        except Exception as e:
            logger.error(f"Error parsing OECD data for {series_id}: {e}")
            raise AdapterError(f"Failed to parse OECD data: {e}")

        # Sort by date
        observations.sort(key=lambda x: x.date)

        return observations

    async def test_connection(self) -> bool:
        """Test connection to OECD API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to fetch a simple dataset
            await self._make_request("MEI", "USA.CPALTT01.IXOB.M", {"detail": "dataonly"})
            return True
        except Exception as e:
            logger.error(f"OECD connection test failed: {e}")
            return False
