# Real-Time Chat Backend Documentation

Welcome to the documentation for the Real-Time Chat Backend project. This is a Slack-like chat application built with Clean Architecture, FastAPI, PostgreSQL, Redis, and Celery.

## Documentation Files

### 1. [Project Overview & PDR](./project-overview-pdr.md)
**Start here** for a high-level understanding of the project.

- Product description and key features
- Technology stack (Python 3.11, FastAPI, PostgreSQL, Redis, Celery, JWT)
- Architecture overview (4-layer Clean Architecture)
- Quality metrics (91.90% test coverage, 379 tests)
- Success criteria and development workflow

### 2. [System Architecture](./system-architecture.md)
Detailed breakdown of the 4-layer Clean Architecture and how data flows through the system.

- Layered architecture diagram
- Complete `src/` directory structure with descriptions
- Data flow example (Send Message journey)
- 4 key architectural patterns (Repository, One Use Case Per Class, Entity-to-Model Conversion, Async-First)
- Database schema and real-time events
- Testing strategy

### 3. [Code Standards](./code-standards.md)
Coding conventions, patterns, and best practices used throughout the project.

- File naming and type hints
- Domain layer patterns (entities, value objects, repositories)
- Use case structure
- Pydantic schemas and API routes
- TDD strategy (unit, integration, E2E tests)
- Exception handling and import organization
- Code coverage requirements (minimum 90%)

### 4. [Codebase Summary](./codebase-summary.md)
Quick reference for the project structure and what exists where.

- Source code breakdown by layer (domain, use cases, adapters, infrastructure)
- Test structure and organization
- Docker setup (4 services: app, PostgreSQL, Redis, Celery worker)
- Database migrations (Alembic)
- Configuration files and key metrics
- 12 feature areas with their use cases (auth, channels, messaging, DMs, threads, files, etc.)

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Start all services (Docker required)
cd docker && docker-compose up --build

# Run tests
pytest --cov=src

# View API docs
# Server runs on http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 379 |
| Code Coverage | 91.90% |
| Language | Python 3.11 |
| Test Types | Unit, Integration, E2E, Performance |
| Architecture | 4-Layer Clean Architecture |
| Max File Size | 200 lines (enforced) |
| Type Hints | Mandatory |

## Feature Areas

The application provides 12 main features:

1. **Authentication** — JWT with access/refresh tokens
2. **Channels** — Public/private channels with membership
3. **Messaging** — Send, edit, delete, history, unread count
4. **Threads** — Nested replies to messages
5. **Direct Messages** — Peer-to-peer conversations
6. **File Uploads** — Async file processing with thumbnails
7. **Mentions** — @mention detection and tagging
8. **Reactions** — Emoji reactions to messages
9. **Search** — Full-text search on messages and channels
10. **Presence** — Real-time online/offline status
11. **Notifications** — In-app notifications for mentions and DMs
12. **WebSocket** — Real-time event streaming via Socket.IO

## Architecture Layers

```
┌─────────────────────────────────────────────┐
│ Frameworks & Drivers                        │
│ (FastAPI, PostgreSQL, Redis, WebSocket)    │
├─────────────────────────────────────────────┤
│ Interface Adapters                          │
│ (API routes, repositories, schemas)        │
├─────────────────────────────────────────────┤
│ Use Cases                                   │
│ (Business logic, one class per action)     │
├─────────────────────────────────────────────┤
│ Domain (Entities)                           │
│ (Pure Python, no framework dependencies)   │
└─────────────────────────────────────────────┘
```

## File Organization

```
src/
├── domain/              # Entities, value objects, repositories (abstract), exceptions
├── use_cases/           # Business logic (80+ classes, one per action)
├── adapters/            # API routes, DB repositories, WebSocket, Redis, Celery
└── infrastructure/      # Config, DI container, logging, app factory

tests/
├── unit/                # Domain and use case tests (isolated)
├── integration/         # Adapter tests against real services
├── e2e/                 # Full user journey tests
└── fakes/               # In-memory mock implementations
```

## How to Navigate

- **First time?** Start with [Project Overview](./project-overview-pdr.md)
- **Understanding architecture?** Read [System Architecture](./system-architecture.md)
- **Writing code?** Refer to [Code Standards](./code-standards.md)
- **Looking for something specific?** Check [Codebase Summary](./codebase-summary.md)

## For Developers

All code follows these principles:

- **YAGNI** — You Aren't Gonna Need It (avoid over-engineering)
- **KISS** — Keep It Simple, Stupid (clarity over cleverness)
- **DRY** — Don't Repeat Yourself (extract common logic)
- **TDD** — Test-Driven Development (tests before code)
- **Clean Architecture** — Separation of concerns, dependency inversion

Type hints are mandatory, async-first design for all I/O, and file size is limited to 200 lines per module.

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test level
pytest tests/unit              # Unit tests only
pytest tests/integration       # Integration tests only
pytest tests/e2e               # E2E tests only

# Run specific test file
pytest tests/unit/use_cases/messaging/test_send_message.py
```

## Support

For questions about:
- **Architecture patterns** → See [System Architecture](./system-architecture.md)
- **Code conventions** → See [Code Standards](./code-standards.md)
- **Project structure** → See [Codebase Summary](./codebase-summary.md)
- **Features and tech stack** → See [Project Overview](./project-overview-pdr.md)

---

**Last Updated:** April 3, 2026  
**Coverage:** 91.90% | **Tests:** 379 | **Status:** Production Ready
