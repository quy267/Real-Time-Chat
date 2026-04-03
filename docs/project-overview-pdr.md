# Real-Time Chat Backend — Product Development Requirements

## Overview

A Slack-like real-time chat backend providing instant messaging, channels, direct messages, threads, file uploads, mentions, reactions, and presence tracking. Built with Clean Architecture principles for maintainability and testability.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11 |
| API Framework | FastAPI 0.115+ |
| Real-time | python-socketio 5.12+ |
| Database | PostgreSQL + SQLAlchemy 2.0 async |
| Cache/Pub-Sub | Redis 5.2+ |
| Task Queue | Celery 5.4+ with Redis broker |
| Authentication | JWT (PyJWT 2.10+) |
| Validation | Pydantic 2.10+ |
| ORM Migrations | Alembic 1.14+ |
| Containerization | Docker + Docker Compose |

## Architecture Style

**4-Layer Clean Architecture:**
```
Entities (Domain) → Use Cases → Interface Adapters → Frameworks & Drivers
```

- **Entities**: Pure Python dataclasses, repository interfaces, exceptions
- **Use Cases**: Business logic (one class per use case), no framework dependencies
- **Adapters**: API routes, database repositories, WebSocket handlers, Celery tasks
- **Frameworks**: FastAPI app, SQLAlchemy session, Redis client, configuration

## Key Features

- **Authentication**: JWT with access/refresh token rotation
- **Channels**: Public/private channel creation, membership management
- **Messaging**: Send, edit, delete messages in channels
- **Threads**: Reply to messages with nested threaded conversations
- **Direct Messages**: Peer-to-peer conversations with history
- **File Uploads**: Upload files to messages with async processing
- **Mentions**: Tag users with @mention detection
- **Reactions**: Add emoji reactions to messages
- **Search**: Full-text search on messages and channels
- **Presence**: Real-time online/offline status tracking
- **Notifications**: In-app notifications for mentions and DMs
- **WebSocket**: Real-time event streaming via Socket.IO

## Quality Metrics

- **Test Coverage**: 92.03% (377 tests)
- **Test Types**: Unit (domain), Integration (adapters), End-to-End (user journeys)
- **Minimum Coverage**: 90%
- **Code Standards**: Type hints, Pydantic schemas, async-first design, dependency injection

## Development Workflow

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests with coverage
pytest --cov=src

# Start services locally
cd docker && docker-compose up --build

# Run API server
uvicorn src.main:app --reload
```

## API Documentation

Interactive Swagger UI available at `/docs` when server runs on http://localhost:8000.

## Success Criteria

- All 377 tests passing
- Code coverage >= 90%
- No N+1 queries in critical paths (optimized with single query methods)
- Real-time messaging < 500ms latency
- Horizontal scalability via async + Redis
- Clean Architecture compliance (dependency rule enforced, no inner→outer imports)
