"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Initializing database...")
    init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Economy Tracker API",
    description="Macroeconomic insights API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Economy Tracker API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and include routers (will be added in later phases)
# from app.api import indicators, series, observations, insights, analytics, alerts, watchlist, notifications, countries
# app.include_router(indicators.router, prefix="/api", tags=["indicators"])
# app.include_router(series.router, prefix="/api", tags=["series"])
# app.include_router(observations.router, prefix="/api", tags=["observations"])
# app.include_router(insights.router, prefix="/api", tags=["insights"])
# app.include_router(analytics.router, prefix="/api", tags=["analytics"])
# app.include_router(alerts.router, prefix="/api", tags=["alerts"])
# app.include_router(watchlist.router, prefix="/api", tags=["watchlist"])
# app.include_router(notifications.router, prefix="/api", tags=["notifications"])
# app.include_router(countries.router, prefix="/api", tags=["countries"])
