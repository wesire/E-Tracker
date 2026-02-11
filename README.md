# Economy Tracker (E-Tracker)

A production-ready macroeconomic insights platform that ingests reliable public data, normalizes it, calculates derived metrics, and presents clear narrative insights across countries and regions.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) API keys for data sources:
  - [FRED API Key](https://fred.stlouisfed.org/docs/api/api_key.html) for U.S. economic data

### Run with Demo Data (No API Keys Required)

```bash
# Clone the repository
git clone https://github.com/wesire/E-Tracker.git
cd E-Tracker

# Copy environment template
cp .env.example .env

# Start all services
docker compose up

# In a new terminal, seed demo data
docker compose exec backend python -m app.seed

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Run with Live Data

1. Get API keys:
   - FRED API Key (required for U.S. data): https://fred.stlouisfed.org/docs/api/api_key.html

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. Start services:
```bash
docker compose up
```

4. The ingestion scheduler will automatically fetch data daily at 6 AM (configurable via `INGESTION_SCHEDULE` in .env)

## 📊 Features

### Data Sources
- **FRED** (Federal Reserve Economic Data): CPI, unemployment, interest rates, GDP
- **World Bank**: GDP growth, inflation, unemployment across countries
- **OECD**: SDMX/JSON format data for international indicators

### Analytics
- **Time Series Calculations**: YoY change, MoM change, QoQ annualized, rolling averages
- **Statistical Analysis**: Z-scores vs 5-year history
- **Regime Classification**: Expansion, Slowdown, Contraction, Recovery
- **Recession Risk Assessment**: Evidence-based heuristics with confidence scores

### Insights
- Deterministic narrative templates (no LLM dependency)
- "What changed?" - Latest value vs previous period
- "Why it matters?" - Contextual explanation
- "Risk signals" - Disinflation, labor softening, yield curve warnings
- All insights cite underlying indicator movements

### User Features
- **Watchlists**: Track specific indicators
- **Alerts**: Set threshold-based alerts with in-app notifications
- **Dashboard**: Key indicators with latest values and sparklines
- **Explorer**: Historical charts with date range selectors
- **Comparison**: Side-by-side country comparisons

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Next.js 14 (TypeScript), Tailwind CSS, shadcn/ui, Recharts
- **Backend**: FastAPI (Python 3.12), SQLAlchemy, Alembic
- **Database**: PostgreSQL with TimescaleDB (graceful fallback to vanilla Postgres)
- **Cache**: Redis
- **Background Jobs**: APScheduler
- **Containerization**: Docker + docker-compose

### Project Structure
```
E-Tracker/
├── backend/
│   ├── app/
│   │   ├── adapters/      # Data source adapters (FRED, World Bank, OECD)
│   │   ├── analytics/     # Calculations, regime classification, recession risk
│   │   ├── insights/      # Narrative insight generation
│   │   ├── api/          # FastAPI routes and schemas
│   │   ├── models/       # SQLAlchemy models
│   │   ├── core/         # Configuration and database setup
│   │   ├── main.py       # FastAPI application
│   │   └── seed.py       # Demo data seeding script
│   ├── migrations/       # Alembic migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities and API client
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── methodology.md    # All formulas and classification rules
│   ├── architecture.md   # System design
│   ├── roadmap.md        # Post-MVP features
│   └── build-log.md      # Implementation log
├── docker-compose.yml
├── .env.example
└── README.md
```

## 📚 Documentation

- **[Methodology](docs/methodology.md)**: All formulas, calculations, and regime classification rules
- **[Architecture](docs/architecture.md)**: System design with diagrams (TODO)
- **[Roadmap](docs/roadmap.md)**: Post-MVP features and enhancements (TODO)

## 🔌 API Endpoints

Full API documentation available at `http://localhost:8000/docs` when running.

### Key Endpoints
- `GET /api/countries` - List available countries
- `GET /api/indicators` - List economic indicators
- `GET /api/series` - List time series with filters
- `GET /api/observations` - Get time series data
- `GET /api/insights` - Get narrative insights for a country
- `GET /api/analytics/regime` - Get economic regime classification
- `GET /api/analytics/recession-risk` - Get recession risk assessment
- `GET /api/status/freshness` - Check data freshness status

### User Features
- `GET/POST/DELETE /api/watchlist` - Manage watchlists
- `GET/POST/PATCH/DELETE /api/alerts` - Manage alerts
- `GET /api/notifications` - Get notifications

## ⚠️ Known Limitations

### MVP Scope
- **No Authentication**: Uses session-based identification (localStorage UUID) for MVP simplicity
- **Limited Country Coverage**: Focused on U.S. data initially, expandable to other countries
- **Rule-Based Insights**: No LLM integration (deterministic templates only)
- **Single Instance**: Not designed for multi-instance deployment yet

### Data Quality
- Economic data is often revised weeks/months after initial release
- Some series have delayed publication schedules
- Missing data points are skipped (not interpolated)
- Z-scores require 60+ periods (5 years) for reliability

### Performance
- No advanced caching strategy beyond Redis TTL
- Database queries not optimized for very large datasets
- Frontend pagination is basic offset/limit

## 🧪 Testing

```bash
# Backend tests
cd backend
pip install -e ".[dev]"
pytest

# Frontend tests
cd frontend
npm test
npm run test:e2e
```

## 🔧 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"

# Run with hot reload
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "Description"
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## 📦 Deployment

For production deployment:

1. Set strong passwords in `.env`
2. Configure CORS appropriately in `backend/app/main.py`
3. Enable HTTPS (use reverse proxy like nginx)
4. Set up proper database backups
5. Monitor ingestion logs and data freshness
6. Consider using managed services (RDS, ElastiCache, etc.)

## 🤝 Contributing

This is a demonstration project. For production use, consider:
- Adding proper authentication and authorization
- Implementing more sophisticated caching strategies
- Adding more data sources and indicators
- Building ML-based forecasting models
- Improving frontend with real-time updates

## 📄 License

This project is for demonstration purposes. Check with data source providers for their terms of use:
- FRED: https://fred.stlouisfed.org/docs/api/terms_of_use.html
- World Bank: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets
- OECD: https://www.oecd.org/termsandconditions/

## 🙏 Acknowledgments

- Federal Reserve Economic Data (FRED) for comprehensive U.S. economic data
- World Bank for international development indicators
- OECD for standardized international statistics
- TimescaleDB for time-series database capabilities

---

**Built with ❤️ for macroeconomic insights**
