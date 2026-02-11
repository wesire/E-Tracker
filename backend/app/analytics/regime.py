"""Economic regime classification."""

from enum import Enum
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.analytics.calculations import AnalyticsEngine
from app.models.models import Indicator, Series


class EconomicRegime(str, Enum):
    """Economic regime classifications."""

    EXPANSION = "expansion"
    SLOWDOWN = "slowdown"
    CONTRACTION = "contraction"
    RECOVERY = "recovery"
    UNKNOWN = "unknown"


class RegimeClassifier:
    """Classifier for determining economic regime."""

    @staticmethod
    def classify_regime(
        db: Session,
        country_id: int,
        gdp_series_id: Optional[int] = None,
        unemployment_series_id: Optional[int] = None,
    ) -> Dict:
        """Classify the economic regime for a country.

        Logic:
        - EXPANSION: GDP growth positive and rising, unemployment falling
        - SLOWDOWN: GDP growth positive but falling, unemployment stable or rising
        - CONTRACTION: GDP growth negative, unemployment rising
        - RECOVERY: GDP growth negative but improving, or positive and accelerating from low, unemployment high but falling

        Args:
            db: Database session
            country_id: Country ID
            gdp_series_id: Optional GDP series ID (will auto-detect if not provided)
            unemployment_series_id: Optional unemployment series ID (will auto-detect if not provided)

        Returns:
            Dictionary with regime classification and supporting data
        """
        # Find GDP and unemployment series if not provided
        if not gdp_series_id:
            gdp_indicator = (
                db.query(Indicator)
                .filter(Indicator.category == "gdp", Indicator.name.ilike("%GDP%"))
                .first()
            )
            if gdp_indicator:
                gdp_series = (
                    db.query(Series)
                    .filter(
                        Series.indicator_id == gdp_indicator.id,
                        Series.country_id == country_id,
                    )
                    .first()
                )
                gdp_series_id = gdp_series.id if gdp_series else None

        if not unemployment_series_id:
            unemployment_indicator = (
                db.query(Indicator)
                .filter(
                    Indicator.category == "employment", Indicator.name.ilike("%unemployment%")
                )
                .first()
            )
            if unemployment_indicator:
                unemployment_series = (
                    db.query(Series)
                    .filter(
                        Series.indicator_id == unemployment_indicator.id,
                        Series.country_id == country_id,
                    )
                    .first()
                )
                unemployment_series_id = unemployment_series.id if unemployment_series else None

        # Get metrics
        gdp_metrics = (
            AnalyticsEngine.calculate_all_metrics(db, gdp_series_id) if gdp_series_id else {}
        )
        unemployment_metrics = (
            AnalyticsEngine.calculate_all_metrics(db, unemployment_series_id)
            if unemployment_series_id
            else {}
        )

        # Extract key indicators
        gdp_growth = gdp_metrics.get("yoy_change")
        gdp_qoq = gdp_metrics.get("qoq_annualized")
        gdp_mom = gdp_metrics.get("mom_change")
        unemployment_rate = unemployment_metrics.get("latest_value")
        unemployment_change = unemployment_metrics.get("yoy_change")

        # Classification logic
        regime = EconomicRegime.UNKNOWN
        confidence = 0.0
        signals = []

        if gdp_growth is not None:
            if gdp_growth > 2.0:  # Strong positive growth
                if unemployment_change is not None and unemployment_change < 0:
                    # Growth accelerating, unemployment falling
                    regime = EconomicRegime.EXPANSION
                    confidence = 0.8
                    signals.append("GDP growth strong and unemployment falling")
                else:
                    # Growth positive but unemployment not improving
                    regime = EconomicRegime.SLOWDOWN
                    confidence = 0.6
                    signals.append("GDP growth positive but unemployment not improving")

            elif gdp_growth > 0:  # Moderate positive growth
                if gdp_mom is not None and gdp_mom < 0:
                    # Growth decelerating
                    regime = EconomicRegime.SLOWDOWN
                    confidence = 0.7
                    signals.append("GDP growth decelerating")
                else:
                    regime = EconomicRegime.EXPANSION
                    confidence = 0.6
                    signals.append("GDP growth moderate and stable")

            else:  # Negative growth
                if (
                    unemployment_change is not None
                    and unemployment_change < 0
                    and unemployment_rate is not None
                    and unemployment_rate > 5.0
                ):
                    # Unemployment falling from high level
                    regime = EconomicRegime.RECOVERY
                    confidence = 0.7
                    signals.append("GDP negative but unemployment falling from elevated levels")
                else:
                    regime = EconomicRegime.CONTRACTION
                    confidence = 0.8
                    signals.append("GDP growth negative")

        return {
            "regime": regime.value,
            "confidence": confidence,
            "signals": signals,
            "gdp_growth_yoy": gdp_growth,
            "gdp_qoq_annualized": gdp_qoq,
            "unemployment_rate": unemployment_rate,
            "unemployment_change_yoy": unemployment_change,
        }
