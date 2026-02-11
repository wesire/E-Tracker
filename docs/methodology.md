# Economic Analysis Methodology

This document describes all formulas, calculations, and classification rules used in the Economy Tracker analytics engine.

## Time Series Calculations

### Year-over-Year (YoY) Change
Percent change compared to the same period one year ago.

```
YoY_change = ((Value_t - Value_t-12) / Value_t-12) × 100
```

Where:
- `Value_t` = Current period value
- `Value_t-12` = Value 12 periods (months) ago

**Use case**: Removes seasonal effects and shows long-term trends.

### Month-over-Month (MoM) Change
Percent change compared to the previous month.

```
MoM_change = ((Value_t - Value_t-1) / Value_t-1) × 100
```

**Use case**: Shows short-term momentum and recent directional changes.

### Quarter-over-Quarter (QoQ) Annualized
Quarterly change expressed as an annualized rate.

```
QoQ_change = (Value_t - Value_t-3) / Value_t-3
QoQ_annualized = ((1 + QoQ_change)^4 - 1) × 100
```

**Use case**: Standard measure for GDP growth, allows comparison across different timeframes.

### Rolling Average
Moving average over a specified window.

```
Rolling_avg_n = (Value_t + Value_t-1 + ... + Value_t-n+1) / n
```

Common windows:
- 3-month: Smooths short-term volatility
- 6-month: Shows medium-term trends

### Z-Score
Standard deviations from historical mean.

```
Z-score = (Value_t - μ) / σ

Where:
μ = Mean(Value_t-60 to Value_t)  # 5-year rolling mean
σ = StdDev(Value_t-60 to Value_t)  # 5-year rolling standard deviation
```

**Interpretation**:
- Z > 2.0: Significantly elevated (top 2.5%)
- Z > 1.0: Moderately elevated
- -1.0 < Z < 1.0: Normal range
- Z < -1.0: Moderately depressed
- Z < -2.0: Significantly depressed (bottom 2.5%)

## Economic Regime Classification

The system classifies economic conditions into four regimes based on GDP growth and unemployment trends.

### Expansion
**Conditions**:
- GDP growth YoY > 2.0% AND
- Unemployment change YoY < 0 (falling)

**Characteristics**: Strong economic growth with improving labor market

### Slowdown
**Conditions**:
- GDP growth YoY > 0% AND (
  - GDP MoM < 0 (decelerating) OR
  - Unemployment change YoY ≥ 0 (not improving)
)

**Characteristics**: Positive but weakening growth, potential early warning

### Contraction
**Conditions**:
- GDP growth YoY < 0% OR
- GDP QoQ annualized < 0 (technical recession: 2 consecutive quarters)

**Characteristics**: Economic decline, official recession conditions

### Recovery
**Conditions**:
- GDP growth < 0% BUT improving trends AND
- Unemployment falling from elevated levels (> 5%) AND
- Unemployment change YoY < 0

**Characteristics**: Emerging from contraction, early recovery phase

### Confidence Scores
Each classification includes a confidence score (0.0 to 1.0):
- 0.8-1.0: Strong signal, clear conditions
- 0.6-0.7: Moderate signal, some ambiguity
- 0.0-0.5: Weak signal, insufficient data or mixed conditions

## Recession Risk Assessment

Recession risk is assessed using multiple evidence-based indicators with known historical predictive power.

### Risk Signals

#### 1. Yield Curve Inversion
**Condition**: 10-Year Treasury Yield - 2-Year Treasury Yield < 0

**Risk weight**: 0.3 (30%)

**Rationale**: Inverted yield curves have preceded every U.S. recession since 1955, typically 12-24 months before onset. Indicates bond market expectations of economic weakness and rate cuts.

#### 2. Rising Unemployment
**Condition**: Unemployment rate YoY change > 0.5 percentage points

**Risk weight**: 0.3 (30%)

**Rationale**: The Sahm Rule identifies recession starts when 3-month average unemployment rises 0.5+ percentage points above its 12-month low. Rising unemployment indicates labor market deterioration.

#### 3. Negative GDP Growth
**Condition**: GDP QoQ annualized < 0%

**Risk weight**: 0.3 (30%)

**Rationale**: Two consecutive quarters of negative GDP growth is the traditional definition of technical recession. Even one negative quarter significantly increases risk.

#### 4. Weak GDP Growth
**Condition**: GDP YoY growth < 1.0%

**Risk weight**: 0.1 (10%)

**Rationale**: Below-trend growth increases vulnerability to shocks and often precedes recession.

#### 5. Elevated Unemployment
**Condition**: Unemployment Z-score > 1.5

**Risk weight**: 0.2 (20%)

**Rationale**: Unemployment well above historical average indicates stressed labor market conditions.

### Risk Levels

Risk scores are calculated by summing the weights of active signals:

- **High Risk** (0.6 - 1.0): Multiple strong signals present, recession likely within 12 months
- **Medium Risk** (0.3 - 0.6): Some warning signals, monitor closely
- **Low Risk** (0.1 - 0.3): Minor concerns, economy likely stable
- **Minimal Risk** (0.0 - 0.1): No significant warning signs

## Insight Generation Templates

### What Changed?
Template structure:
```
[Country] [Indicator] [direction] [change magnitude] [units] as of [date].
```

Direction determination:
- |YoY change| < 0.1%: "remained stable"
- YoY change > 0: "increased"
- YoY change < 0: "decreased"

### Why It Matters?
Contextual explanation based on indicator category:

**GDP**: Broadest measure of economic activity and growth
**Inflation**: Price stability and purchasing power
**Unemployment**: Labor market health and economic capacity
**Interest Rates**: Borrowing costs and monetary policy stance

Each includes Z-score interpretation for historical context.

### Risk Signals
Indicator-specific warnings:

**Inflation**:
- Disinflation: YoY change < -1.0%
- Elevated inflation: YoY change > 2.0%

**Unemployment**:
- Labor softening: YoY change > 0.5 pp
- Elevated unemployment: Z-score > 1.5

**GDP**:
- Negative growth: YoY < 0%
- Weak growth: YoY < 1.0%

**Interest Rates**:
- Yield curve inversion: Value < 0

## Data Quality and Limitations

### Missing Data Handling
- Observations with missing values (`.` in FRED, `null` in APIs) are skipped
- Calculations requiring N periods fail gracefully if insufficient data
- Z-scores require minimum 60 periods (5 years monthly) for reliability

### Frequency Assumptions
- **Monthly data**: Default assumption for most calculations
- **Quarterly data**: QoQ calculations use 3-period lag
- **Annual data**: Limited to YoY comparisons

### Seasonal Adjustment
- Series metadata includes seasonal adjustment flag
- Non-seasonally adjusted data may show misleading MoM changes
- YoY comparisons mitigate seasonal effects regardless

### Revisions and Vintages
- Economic data is often revised weeks or months after initial release
- System tracks `vintage_date` when available
- Latest revision is used for analysis (most agencies report final revisions)

## References

- **Sahm Rule**: Sahm, Claudia (2019). "Direct Stimulus Payments to Individuals"
- **Yield Curve Inversions**: Federal Reserve research papers on predictive power
- **Business Cycle Dating**: NBER Business Cycle Dating Committee methodology
- **Technical Recession**: Common definition of 2 consecutive quarters of negative GDP growth

## Future Enhancements

Planned additions (not yet implemented):
- Nowcasting models using high-frequency data
- Machine learning recession probability models
- Real-time revision tracking and impact analysis
- Cross-country correlation analysis
- Sector-specific leading indicators
