"""Analytics calculations for economic data."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import Observation, Series


class AnalyticsEngine:
    """Engine for performing analytics calculations on economic data."""

    @staticmethod
    def get_series_data(
        db: Session, series_id: int, start_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get series data as a pandas DataFrame.

        Args:
            db: Database session
            series_id: Series ID
            start_date: Optional start date filter

        Returns:
            DataFrame with columns: date, value
        """
        query = db.query(Observation).filter(Observation.series_id == series_id)

        if start_date:
            query = query.filter(Observation.observation_date >= start_date)

        observations = query.order_by(Observation.observation_date).all()

        if not observations:
            return pd.DataFrame(columns=["date", "value"])

        df = pd.DataFrame(
            [(obs.observation_date, obs.value) for obs in observations],
            columns=["date", "value"],
        )
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        return df

    @staticmethod
    def calculate_yoy_change(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate year-over-year percent change.

        Args:
            df: DataFrame with date index and value column

        Returns:
            DataFrame with additional yoy_change column
        """
        if df.empty:
            return df

        df = df.copy()
        df["yoy_change"] = df["value"].pct_change(periods=12) * 100

        return df

    @staticmethod
    def calculate_mom_change(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate month-over-month percent change.

        Args:
            df: DataFrame with date index and value column

        Returns:
            DataFrame with additional mom_change column
        """
        if df.empty:
            return df

        df = df.copy()
        df["mom_change"] = df["value"].pct_change(periods=1) * 100

        return df

    @staticmethod
    def calculate_qoq_annualized(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate quarter-over-quarter annualized percent change.

        Args:
            df: DataFrame with date index and value column

        Returns:
            DataFrame with additional qoq_annualized column
        """
        if df.empty:
            return df

        df = df.copy()
        qoq_change = df["value"].pct_change(periods=3)
        df["qoq_annualized"] = ((1 + qoq_change) ** 4 - 1) * 100

        return df

    @staticmethod
    def calculate_rolling_average(df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
        """Calculate rolling average.

        Args:
            df: DataFrame with date index and value column
            window: Window size in periods (default: 3)

        Returns:
            DataFrame with additional rolling_avg column
        """
        if df.empty:
            return df

        df = df.copy()
        df[f"rolling_avg_{window}m"] = df["value"].rolling(window=window).mean()

        return df

    @staticmethod
    def calculate_zscore(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
        """Calculate Z-score vs historical data.

        Args:
            df: DataFrame with date index and value column
            window: Window size in periods for calculating mean/std (default: 60 = 5 years monthly)

        Returns:
            DataFrame with additional zscore column
        """
        if df.empty or len(df) < window:
            return df

        df = df.copy()
        rolling_mean = df["value"].rolling(window=window).mean()
        rolling_std = df["value"].rolling(window=window).std()
        df["zscore"] = (df["value"] - rolling_mean) / rolling_std

        return df

    @staticmethod
    def get_latest_value(db: Session, series_id: int) -> Optional[Tuple[datetime, float]]:
        """Get the latest value for a series.

        Args:
            db: Database session
            series_id: Series ID

        Returns:
            Tuple of (date, value) or None if no data
        """
        observation = (
            db.query(Observation)
            .filter(Observation.series_id == series_id)
            .order_by(Observation.observation_date.desc())
            .first()
        )

        if observation:
            return (observation.observation_date, observation.value)
        return None

    @staticmethod
    def get_change_over_period(
        db: Session, series_id: int, months_back: int = 12
    ) -> Optional[float]:
        """Calculate percent change over a specified period.

        Args:
            db: Database session
            series_id: Series ID
            months_back: Number of months to look back (default: 12 for YoY)

        Returns:
            Percent change or None if insufficient data
        """
        latest = AnalyticsEngine.get_latest_value(db, series_id)
        if not latest:
            return None

        latest_date, latest_value = latest

        # Get value from months_back ago
        target_date = latest_date - timedelta(days=months_back * 30)

        previous = (
            db.query(Observation)
            .filter(
                Observation.series_id == series_id, Observation.observation_date <= target_date
            )
            .order_by(Observation.observation_date.desc())
            .first()
        )

        if previous and previous.value != 0:
            return ((latest_value - previous.value) / previous.value) * 100

        return None

    @staticmethod
    def calculate_all_metrics(db: Session, series_id: int) -> dict:
        """Calculate all analytics metrics for a series.

        Args:
            db: Database session
            series_id: Series ID

        Returns:
            Dictionary with all calculated metrics
        """
        # Get data for last 10 years
        start_date = datetime.utcnow() - timedelta(days=3650)
        df = AnalyticsEngine.get_series_data(db, series_id, start_date)

        if df.empty:
            return {}

        # Calculate all metrics
        df = AnalyticsEngine.calculate_yoy_change(df)
        df = AnalyticsEngine.calculate_mom_change(df)
        df = AnalyticsEngine.calculate_qoq_annualized(df)
        df = AnalyticsEngine.calculate_rolling_average(df, window=3)
        df = AnalyticsEngine.calculate_rolling_average(df, window=6)
        df = AnalyticsEngine.calculate_zscore(df, window=60)

        # Get latest values
        latest = df.iloc[-1] if not df.empty else None

        if latest is None:
            return {}

        metrics = {
            "latest_date": df.index[-1].to_pydatetime(),
            "latest_value": float(latest["value"]) if not pd.isna(latest["value"]) else None,
            "yoy_change": float(latest["yoy_change"])
            if not pd.isna(latest.get("yoy_change"))
            else None,
            "mom_change": float(latest["mom_change"])
            if not pd.isna(latest.get("mom_change"))
            else None,
            "qoq_annualized": float(latest["qoq_annualized"])
            if not pd.isna(latest.get("qoq_annualized"))
            else None,
            "rolling_avg_3m": float(latest["rolling_avg_3m"])
            if not pd.isna(latest.get("rolling_avg_3m"))
            else None,
            "rolling_avg_6m": float(latest["rolling_avg_6m"])
            if not pd.isna(latest.get("rolling_avg_6m"))
            else None,
            "zscore": float(latest["zscore"]) if not pd.isna(latest.get("zscore")) else None,
        }

        return metrics
