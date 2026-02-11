"""Seed script to populate demo data for quick preview."""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, init_db
from app.models.models import Country, Indicator, IndicatorCategory, Observation, Series


def create_demo_country(db: Session) -> Country:
    """Create or get demo country (United States)."""
    country = db.query(Country).filter(Country.iso_alpha3 == "USA").first()
    if country:
        return country

    country = Country(
        name="United States",
        iso_alpha2="US",
        iso_alpha3="USA",
        region="North America",
    )
    db.add(country)
    db.commit()
    db.refresh(country)
    print(f"Created country: {country.name}")
    return country


def create_demo_indicators(db: Session) -> list[Indicator]:
    """Create demo indicators."""
    indicators_data = [
        {
            "name": "Consumer Price Index (CPI)",
            "description": "Measure of average change in prices paid by consumers",
            "category": IndicatorCategory.INFLATION,
            "unit": "index",
            "default_frequency": "monthly",
        },
        {
            "name": "Unemployment Rate",
            "description": "Percentage of labor force that is unemployed",
            "category": IndicatorCategory.EMPLOYMENT,
            "unit": "percent",
            "default_frequency": "monthly",
        },
        {
            "name": "Gross Domestic Product",
            "description": "Total value of goods and services produced",
            "category": IndicatorCategory.GDP,
            "unit": "billions",
            "default_frequency": "quarterly",
        },
        {
            "name": "Federal Funds Rate",
            "description": "Target interest rate set by the Federal Reserve",
            "category": IndicatorCategory.INTEREST_RATE,
            "unit": "percent",
            "default_frequency": "monthly",
        },
        {
            "name": "10Y-2Y Treasury Spread",
            "description": "Difference between 10-year and 2-year Treasury yields",
            "category": IndicatorCategory.INTEREST_RATE,
            "unit": "percent",
            "default_frequency": "daily",
        },
    ]

    indicators = []
    for ind_data in indicators_data:
        existing = db.query(Indicator).filter(Indicator.name == ind_data["name"]).first()
        if existing:
            indicators.append(existing)
            continue

        indicator = Indicator(**ind_data)
        db.add(indicator)
        indicators.append(indicator)

    db.commit()
    for ind in indicators:
        db.refresh(ind)
    print(f"Created {len(indicators)} indicators")
    return indicators


def create_demo_series(db: Session, country: Country, indicators: list[Indicator]) -> list[Series]:
    """Create demo series."""
    series_list = []

    for indicator in indicators:
        existing = (
            db.query(Series)
            .filter(
                Series.indicator_id == indicator.id,
                Series.country_id == country.id,
            )
            .first()
        )
        if existing:
            series_list.append(existing)
            continue

        series = Series(
            indicator_id=indicator.id,
            country_id=country.id,
            source="DEMO",
            source_series_id=f"DEMO_{indicator.name[:10].upper().replace(' ', '_')}",
            frequency=indicator.default_frequency,
            seasonal_adjustment="seasonally_adjusted",
        )
        db.add(series)
        series_list.append(series)

    db.commit()
    for s in series_list:
        db.refresh(s)
    print(f"Created {len(series_list)} series")
    return series_list


def generate_demo_observations(db: Session, series_list: list[Series]):
    """Generate synthetic demo observations."""
    import random

    end_date = datetime.now()
    start_date = end_date - timedelta(days=3650)  # 10 years

    for series in series_list:
        # Skip if already has data
        existing_count = db.query(Observation).filter(Observation.series_id == series.id).count()
        if existing_count > 0:
            print(f"Series {series.id} already has data, skipping")
            continue

        # Generate monthly data
        current_date = start_date
        base_value = random.uniform(50, 200)
        trend = random.uniform(-0.5, 1.5)

        observations = []
        while current_date <= end_date:
            # Add some noise and trend
            value = base_value + (current_date - start_date).days / 365 * trend
            value += random.gauss(0, 5)  # Add noise

            obs = Observation(
                series_id=series.id,
                observation_date=current_date,
                value=max(0, value),  # Ensure non-negative
            )
            observations.append(obs)

            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        db.bulk_save_objects(observations)
        db.commit()
        print(f"Created {len(observations)} observations for series {series.id}")


def seed_demo_data():
    """Main function to seed demo data."""
    print("Initializing database...")
    init_db()

    db = SessionLocal()
    try:
        print("Creating demo country...")
        country = create_demo_country(db)

        print("Creating demo indicators...")
        indicators = create_demo_indicators(db)

        print("Creating demo series...")
        series_list = create_demo_series(db, country, indicators)

        print("Generating demo observations...")
        generate_demo_observations(db, series_list)

        print("\n✅ Demo data seeded successfully!")
        print(f"Created:")
        print(f"  - 1 country: {country.name}")
        print(f"  - {len(indicators)} indicators")
        print(f"  - {len(series_list)} series")
        print(f"  - Observations for 10 years of monthly data")
        print("\nYou can now start the application and explore the demo data.")

    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
