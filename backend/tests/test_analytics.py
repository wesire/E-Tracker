"""Test analytics calculations."""

import pandas as pd
from datetime import datetime, timedelta

from app.analytics.calculations import AnalyticsEngine


def test_calculate_yoy_change():
    """Test year-over-year change calculation."""
    # Create sample data
    dates = pd.date_range(start='2020-01-01', periods=24, freq='MS')
    values = [100 + i for i in range(24)]
    df = pd.DataFrame({'value': values}, index=dates)

    # Calculate YoY change
    result = AnalyticsEngine.calculate_yoy_change(df)

    # Check that YoY change is calculated
    assert 'yoy_change' in result.columns
    assert not result['yoy_change'].iloc[-1] == 0  # Should have some change


def test_calculate_mom_change():
    """Test month-over-month change calculation."""
    dates = pd.date_range(start='2020-01-01', periods=12, freq='MS')
    values = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122]
    df = pd.DataFrame({'value': values}, index=dates)

    result = AnalyticsEngine.calculate_mom_change(df)

    assert 'mom_change' in result.columns
    # All changes should be approximately 2%
    assert result['mom_change'].iloc[-1] > 0


def test_calculate_rolling_average():
    """Test rolling average calculation."""
    dates = pd.date_range(start='2020-01-01', periods=12, freq='MS')
    values = [100] * 12
    df = pd.DataFrame({'value': values}, index=dates)

    result = AnalyticsEngine.calculate_rolling_average(df, window=3)

    assert 'rolling_avg_3m' in result.columns
    # With constant values, rolling avg should equal the value
    assert result['rolling_avg_3m'].iloc[-1] == 100


def test_calculate_zscore():
    """Test Z-score calculation."""
    # Create data with enough periods
    dates = pd.date_range(start='2015-01-01', periods=72, freq='MS')
    values = [100] * 60 + [120] * 12  # Last year has higher values
    df = pd.DataFrame({'value': values}, index=dates)

    result = AnalyticsEngine.calculate_zscore(df, window=60)

    assert 'zscore' in result.columns
    # Last values should have positive Z-score (above average)
    assert result['zscore'].iloc[-1] > 0
