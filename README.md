# Backend Service Documentation

## Directory Structure Overview

```
test-backend/
├── app/                    # Main application directory
│   ├── __init__.py        # Application factory and extensions
│   ├── models.py          # Database models
│   ├── routes.py          # API endpoints
│   └── services/          # Business logic services
│       ├── email_service.py    # Email handling
│       └── stripe_service.py   # Payment processing
├── migrations/            # Database migration files
├── monitoring/           # Observability stack
│   ├── grafana/         # Metrics visualization
│   ├── loki/           # Log aggregation
│   └── prometheus/     # Metrics collection
└── terraform/          # Infrastructure as Code
    ├── dev/
    ├── staging/
    └── prod/
```

## Core Components

### Application Stack
- **Framework**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based authentication
- **API**: RESTful endpoints with Flask-CORS support

### Key Dependencies
```toml
- flask>=3.1.2
- flask-sqlalchemy>=3.1.1
- flask-migrate>=4.1.0
- flask-cors>=6.0.1
- flask-jwt-extended>=4.7.1
- sentry-sdk[flask]
- prometheus-flask-exporter
```

## Monitoring Stack
1. **Prometheus**: Metrics collection and storage
2. **Grafana**: Metrics visualization and dashboards
3. **Loki**: Log aggregation and querying
4. **Sentry**: Error tracking and performance monitoring

## Infrastructure
- **Docker**: Containerized deployment using docker-compose
- **Terraform**: Infrastructure provisioning for multiple environments
  - Development
  - Staging
  - Production

## Key Features
1. **Database Management**
   - SQLAlchemy models
   - Alembic migrations
   - PostgreSQL database

2. **API Services**
   - Email service integration
   - Stripe payment processing
   - CORS-enabled endpoints

3. **Observability**
   - Prometheus metrics
   - Grafana dashboards
   - Loki log aggregation
   - Sentry error tracking

4. **Security**
   - JWT authentication
   - CORS protection
   - Environment-based configurations

## Development Setup

### Local Development
1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up environment variables:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   DATABASE_URL=postgresql://myuser:mypassword@db:5432/mytemplate_db
   ```

3. Start services:
   ```bash
   docker-compose up
   ```

### Database Management
- Migrations are handled through Flask-Migrate
- Initial schema is defined in migrations/versions/

## Monitoring Access
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

## Container Structure
- Web Server: Flask application (port 5000)
- Database: PostgreSQL (port 5432)
- Monitoring:
  - Prometheus (port 9090)
  - Grafana (port 3000)
  - Loki (port 3100)

## Note for LLMs
This structure follows a modular architecture with clear separation of concerns:
- Business logic in services/
- Data models in models.py
- Routes in routes.py
- Infrastructure as Code in terraform/
- Monitoring and observability in monitoring/

When analyzing this codebase, focus on:
1. The app/ directory for application logic
2. The monitoring/ directory for observability setup
3. The terraform/ directory for infrastructure configuration
