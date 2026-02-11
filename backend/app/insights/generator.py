"""Insight generation with narrative templates."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.analytics.calculations import AnalyticsEngine
from app.analytics.recession_risk import RecessionRiskAssessor
from app.analytics.regime import RegimeClassifier
from app.models.models import Indicator, IndicatorCategory, Series


class InsightGenerator:
    """Generate narrative insights from economic data."""

    @staticmethod
    def generate_indicator_insight(db: Session, series_id: int) -> Dict:
        """Generate insight for a specific indicator series.

        Args:
            db: Database session
            series_id: Series ID

        Returns:
            Dictionary with insight narrative
        """
        # Get series and indicator info
        series = db.query(Series).filter(Series.id == series_id).first()
        if not series:
            return {"error": "Series not found"}

        indicator = db.query(Indicator).filter(Indicator.id == series.indicator_id).first()
        country = series.country

        # Calculate metrics
        metrics = AnalyticsEngine.calculate_all_metrics(db, series_id)
        if not metrics:
            return {"error": "Insufficient data for analysis"}

        # Generate narrative
        latest_date = metrics.get("latest_date")
        latest_value = metrics.get("latest_value")
        yoy_change = metrics.get("yoy_change")
        mom_change = metrics.get("mom_change")

        # What changed?
        what_changed = InsightGenerator._generate_what_changed(
            indicator, country.name, latest_date, latest_value, yoy_change, mom_change
        )

        # Why it matters?
        why_it_matters = InsightGenerator._generate_why_it_matters(indicator, metrics)

        # Risk signals
        risk_signals = InsightGenerator._generate_risk_signals(indicator, metrics)

        return {
            "series_id": series_id,
            "indicator_name": indicator.name,
            "country_name": country.name,
            "latest_date": latest_date,
            "what_changed": what_changed,
            "why_it_matters": why_it_matters,
            "risk_signals": risk_signals,
            "metrics": metrics,
        }

    @staticmethod
    def _generate_what_changed(
        indicator: Indicator,
        country_name: str,
        latest_date: datetime,
        latest_value: float,
        yoy_change: Optional[float],
        mom_change: Optional[float],
    ) -> str:
        """Generate 'What changed?' narrative."""
        date_str = latest_date.strftime("%B %Y")
        direction = ""
        change_desc = ""

        if yoy_change is not None:
            if abs(yoy_change) < 0.1:
                direction = "remained stable"
                change_desc = f"at {latest_value:.2f}"
            elif yoy_change > 0:
                direction = "increased"
                change_desc = f"by {abs(yoy_change):.1f}% year-over-year to {latest_value:.2f}"
            else:
                direction = "decreased"
                change_desc = f"by {abs(yoy_change):.1f}% year-over-year to {latest_value:.2f}"
        else:
            change_desc = f"stands at {latest_value:.2f}"

        unit = indicator.unit or ""
        unit_suffix = f" {unit}" if unit and unit not in ["percent", "index"] else ""

        return (
            f"{country_name} {indicator.name} {direction} {change_desc}{unit_suffix} "
            f"as of {date_str}."
        )

    @staticmethod
    def _generate_why_it_matters(indicator: Indicator, metrics: Dict) -> str:
        """Generate 'Why it matters?' narrative based on indicator category."""
        category = indicator.category
        zscore = metrics.get("zscore")

        if category == IndicatorCategory.GDP:
            return (
                "GDP growth is the broadest measure of economic activity. "
                "Strong GDP growth indicates economic expansion, while declining GDP suggests contraction. "
                f"The current level is {InsightGenerator._zscore_interpretation(zscore)} relative to historical norms."
            )

        elif category == IndicatorCategory.INFLATION:
            return (
                "Inflation measures the rate of price increases in the economy. "
                "High inflation erodes purchasing power, while very low inflation may signal weak demand. "
                "Central banks typically target 2% inflation. "
                f"The current level is {InsightGenerator._zscore_interpretation(zscore)} relative to historical norms."
            )

        elif category == IndicatorCategory.EMPLOYMENT:
            return (
                "Unemployment is a key indicator of labor market health. "
                "Rising unemployment signals economic weakness, while falling unemployment indicates strength. "
                "Low unemployment can also lead to wage pressures and inflation. "
                f"The current level is {InsightGenerator._zscore_interpretation(zscore)} relative to historical norms."
            )

        elif category == IndicatorCategory.INTEREST_RATE:
            return (
                "Interest rates influence borrowing costs and economic activity. "
                "Higher rates slow growth and reduce inflation, while lower rates stimulate the economy. "
                "Yield curve inversions (short rates > long rates) have historically preceded recessions."
            )

        else:
            return (
                "This indicator provides insights into economic conditions and trends. "
                "Monitoring changes helps assess the overall economic outlook."
            )

    @staticmethod
    def _zscore_interpretation(zscore: Optional[float]) -> str:
        """Interpret Z-score value."""
        if zscore is None:
            return "within normal range"

        if zscore > 2.0:
            return "significantly elevated compared to"
        elif zscore > 1.0:
            return "moderately above"
        elif zscore > 0.5:
            return "slightly above"
        elif zscore > -0.5:
            return "near"
        elif zscore > -1.0:
            return "slightly below"
        elif zscore > -2.0:
            return "moderately below"
        else:
            return "significantly below"

    @staticmethod
    def _generate_risk_signals(indicator: Indicator, metrics: Dict) -> List[str]:
        """Generate risk signals based on indicator movements."""
        signals = []
        category = indicator.category
        yoy_change = metrics.get("yoy_change")
        mom_change = metrics.get("mom_change")
        zscore = metrics.get("zscore")

        if category == IndicatorCategory.INFLATION:
            if yoy_change is not None and yoy_change < -1.0:
                signals.append("Disinflation: Prices growing slower than last year, may indicate weakening demand")
            elif yoy_change is not None and yoy_change > 2.0:
                signals.append("Elevated inflation: Price growth accelerating, central banks may tighten policy")

        elif category == IndicatorCategory.EMPLOYMENT:
            if yoy_change is not None and yoy_change > 0.5:
                signals.append("Labor softening: Unemployment rising, suggests weakening economy")
            elif zscore is not None and zscore > 1.5:
                signals.append("Elevated unemployment: Well above historical average, recession signal")

        elif category == IndicatorCategory.GDP:
            if yoy_change is not None and yoy_change < 0:
                signals.append("Negative growth: Economy contracting, recession risk elevated")
            elif yoy_change is not None and yoy_change < 1.0:
                signals.append("Weak growth: Below-trend expansion, watch for further deterioration")

        elif category == IndicatorCategory.INTEREST_RATE:
            latest_value = metrics.get("latest_value")
            if latest_value is not None and latest_value < 0:
                signals.append("Yield curve inversion: Historically reliable recession indicator, persisting inversion increases risk")

        return signals

    @staticmethod
    def generate_country_insights(db: Session, country_id: int) -> Dict:
        """Generate comprehensive insights for a country.

        Args:
            db: Database session
            country_id: Country ID

        Returns:
            Dictionary with all insights for the country
        """
        # Get regime classification
        regime_data = RegimeClassifier.classify_regime(db, country_id)

        # Get recession risk
        recession_risk = RecessionRiskAssessor.assess_recession_risk(db, country_id)

        # Get all series for the country
        series_list = db.query(Series).filter(Series.country_id == country_id).all()

        # Generate insights for key indicators
        indicator_insights = []
        for series in series_list[:5]:  # Limit to top 5 for now
            insight = InsightGenerator.generate_indicator_insight(db, series.id)
            if "error" not in insight:
                indicator_insights.append(insight)

        return {
            "country_id": country_id,
            "regime": regime_data,
            "recession_risk": recession_risk,
            "indicator_insights": indicator_insights,
            "generated_at": datetime.utcnow(),
        }
