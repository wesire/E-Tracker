"""Recession risk assessment."""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.analytics.calculations import AnalyticsEngine
from app.models.models import Indicator, Series


class RecessionRiskAssessor:
    """Assess recession risk based on multiple indicators."""

    @staticmethod
    def assess_recession_risk(
        db: Session,
        country_id: int,
        gdp_series_id: Optional[int] = None,
        unemployment_series_id: Optional[int] = None,
        yield_curve_series_id: Optional[int] = None,
    ) -> Dict:
        """Assess recession risk for a country.

        Risk signals:
        1. Yield curve inversion (10Y-2Y < 0)
        2. Rising unemployment (YoY change > 0.5 percentage points)
        3. Declining GDP (QoQ < 0 for 2+ quarters)
        4. High unemployment Z-score (> 1.5)

        Args:
            db: Database session
            country_id: Country ID
            gdp_series_id: Optional GDP series ID
            unemployment_series_id: Optional unemployment series ID
            yield_curve_series_id: Optional yield curve series ID

        Returns:
            Dictionary with risk assessment
        """
        # Find series if not provided
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

        if not yield_curve_series_id:
            yield_indicator = (
                db.query(Indicator)
                .filter(
                    Indicator.category == "interest_rate",
                    Indicator.name.ilike("%yield%spread%"),
                )
                .first()
            )
            if yield_indicator:
                yield_series = (
                    db.query(Series)
                    .filter(
                        Series.indicator_id == yield_indicator.id,
                        Series.country_id == country_id,
                    )
                    .first()
                )
                yield_curve_series_id = yield_series.id if yield_series else None

        # Calculate metrics
        gdp_metrics = (
            AnalyticsEngine.calculate_all_metrics(db, gdp_series_id) if gdp_series_id else {}
        )
        unemployment_metrics = (
            AnalyticsEngine.calculate_all_metrics(db, unemployment_series_id)
            if unemployment_series_id
            else {}
        )
        yield_metrics = (
            AnalyticsEngine.calculate_all_metrics(db, yield_curve_series_id)
            if yield_curve_series_id
            else {}
        )

        # Evaluate risk signals
        risk_signals: List[Dict] = []
        risk_score = 0.0

        # 1. Yield curve inversion
        yield_curve_value = yield_metrics.get("latest_value")
        if yield_curve_value is not None and yield_curve_value < 0:
            risk_signals.append(
                {
                    "signal": "Yield curve inverted",
                    "description": f"10Y-2Y spread is {yield_curve_value:.2f}%, indicating inverted yield curve",
                    "severity": "high",
                }
            )
            risk_score += 0.3

        # 2. Rising unemployment
        unemployment_change = unemployment_metrics.get("yoy_change")
        if unemployment_change is not None and unemployment_change > 0.5:
            risk_signals.append(
                {
                    "signal": "Rising unemployment",
                    "description": f"Unemployment increased {unemployment_change:.1f} percentage points YoY",
                    "severity": "high",
                }
            )
            risk_score += 0.3

        # 3. Declining GDP
        gdp_qoq = gdp_metrics.get("qoq_annualized")
        gdp_growth = gdp_metrics.get("yoy_change")
        if gdp_qoq is not None and gdp_qoq < 0:
            risk_signals.append(
                {
                    "signal": "Negative GDP growth",
                    "description": f"GDP declined {gdp_qoq:.1f}% QoQ annualized",
                    "severity": "high",
                }
            )
            risk_score += 0.3
        elif gdp_growth is not None and gdp_growth < 1.0:
            risk_signals.append(
                {
                    "signal": "Weak GDP growth",
                    "description": f"GDP growth at {gdp_growth:.1f}% YoY, below trend",
                    "severity": "medium",
                }
            )
            risk_score += 0.1

        # 4. Elevated unemployment
        unemployment_zscore = unemployment_metrics.get("zscore")
        if unemployment_zscore is not None and unemployment_zscore > 1.5:
            risk_signals.append(
                {
                    "signal": "Elevated unemployment",
                    "description": f"Unemployment Z-score at {unemployment_zscore:.2f}, well above historical average",
                    "severity": "medium",
                }
            )
            risk_score += 0.2

        # Determine risk level
        if risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        elif risk_score > 0:
            risk_level = "low"
        else:
            risk_level = "minimal"

        return {
            "risk_level": risk_level,
            "risk_score": min(risk_score, 1.0),
            "risk_signals": risk_signals,
            "metrics": {
                "gdp_growth_yoy": gdp_growth,
                "gdp_qoq_annualized": gdp_qoq,
                "unemployment_rate": unemployment_metrics.get("latest_value"),
                "unemployment_change_yoy": unemployment_change,
                "yield_curve_spread": yield_curve_value,
            },
        }
