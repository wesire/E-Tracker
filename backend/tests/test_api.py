"""Test API endpoints."""

from app.models.models import Country, Indicator, IndicatorCategory


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "Economy Tracker API"


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_countries_empty(client):
    """Test listing countries when none exist."""
    response = client.get("/api/countries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_countries_with_data(client, db):
    """Test listing countries with data."""
    # Add a country
    country = Country(
        name="United States",
        iso_alpha2="US",
        iso_alpha3="USA",
        region="North America"
    )
    db.add(country)
    db.commit()

    response = client.get("/api/countries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "United States"


def test_list_indicators_empty(client):
    """Test listing indicators when none exist."""
    response = client.get("/api/indicators")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_indicators_with_data(client, db):
    """Test listing indicators with data."""
    # Add an indicator
    indicator = Indicator(
        name="Consumer Price Index",
        description="Measure of inflation",
        category=IndicatorCategory.INFLATION,
        unit="index",
        default_frequency="monthly"
    )
    db.add(indicator)
    db.commit()

    response = client.get("/api/indicators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Consumer Price Index"


def test_get_nonexistent_country(client):
    """Test getting a country that doesn't exist."""
    response = client.get("/api/countries/999")
    assert response.status_code == 404


def test_status_freshness(client):
    """Test data freshness status endpoint."""
    response = client.get("/api/status/freshness")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert "overall_status" in data
