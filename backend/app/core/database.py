"""Database setup and session management."""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Create engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database and enable TimescaleDB if configured."""
    from app.models import models  # noqa: F401

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Try to enable TimescaleDB for observations table if configured
    if settings.enable_timescaledb:
        try:
            with engine.connect() as conn:
                # Check if TimescaleDB extension exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
                )
                if not result.fetchone():
                    # Try to create extension
                    try:
                        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
                        conn.commit()
                    except Exception:
                        print("TimescaleDB extension not available, using vanilla PostgreSQL")
                        return

                # Convert observations table to hypertable if not already
                try:
                    conn.execute(
                        text(
                            "SELECT create_hypertable('observations', 'observation_date', "
                            "if_not_exists => TRUE, migrate_data => TRUE)"
                        )
                    )
                    conn.commit()
                    print("TimescaleDB hypertable enabled for observations")
                except Exception as e:
                    print(f"Could not create hypertable (may already exist): {e}")
        except Exception as e:
            print(f"TimescaleDB setup failed, using vanilla PostgreSQL: {e}")
