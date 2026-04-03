# Real-Time Chat Backend

Slack-like real-time chat backend built with Clean Architecture.

## Tech Stack

- **Framework:** FastAPI + python-socketio
- **Database:** PostgreSQL (SQLAlchemy 2.0 async)
- **Cache/Pub-Sub:** Redis
- **Task Queue:** Celery
- **Auth:** JWT (access + refresh tokens)
- **Containerization:** Docker

## Architecture

4-layer Clean Architecture:

```
Entities → Use Cases → Interface Adapters → Frameworks & Drivers
```

## Quick Start

```bash
# Start all services
cd docker && docker-compose up --build

# Run tests
cd docker && docker-compose -f docker-compose.yml -f docker-compose.test.yml up --build

# Local development (requires PostgreSQL + Redis running)
pip install -e ".[dev]"
uvicorn src.main:app --reload
```

## API Docs

With the server running: http://localhost:8000/docs

## Project Structure

```
src/
  domain/          # Entities, value objects, repository interfaces
  use_cases/       # Business logic (one class per use case)
  adapters/        # API routes, DB repos, Redis, WebSocket, Celery
  infrastructure/  # Config, DI container, logging
  main.py          # App entry point
tests/
  unit/            # Domain + use case tests
  integration/     # Adapter tests against real services
  e2e/             # Full user journey tests
docker/            # Dockerfile + Compose files
alembic/           # Database migrations
```

## Testing

```bash
pytest                          # Run all tests
pytest --cov=src               # With coverage report
pytest tests/unit              # Unit tests only
pytest tests/integration       # Integration tests only
```
