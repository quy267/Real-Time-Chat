# Codebase Summary

## Source Code Structure (`src/`)

### `domain/` — Pure Business Rules

**Entities** (dataclasses, no framework dependencies):
- `entities/user.py` — User account with email, username, status
- `entities/channel.py` — Channel with name, description, privacy level
- `entities/message.py` — Message in channel with content, timestamps
- `entities/thread.py` — Threaded reply to message
- `entities/direct_message.py` — Peer-to-peer message
- `entities/file.py` — Uploaded file metadata
- `entities/reaction.py` — Emoji reaction to message
- `entities/notification.py` — User notification with read status

**Value Objects** (immutable domain concepts):
- `value_objects/token_pair.py` — JWT access + refresh tokens
- `value_objects/presence_status.py` — Online/offline/away status enum

**Repository Interfaces** (ABC, no implementation):
- `repositories/user_repository.py` — Abstract user persistence
- `repositories/channel_repository.py` — Abstract channel persistence
- `repositories/message_repository.py` — Abstract message persistence
- `repositories/token_service.py` — Abstract JWT token creation/validation
- `repositories/password_service.py` — Abstract password hashing/verification
- (+ repositories for threads, DMs, files, reactions, notifications)

**Exceptions** (domain-level errors):
- `exceptions.py` — EntityNotFoundError, DuplicateEntityError, ValidationError, AuthenticationError, AuthorizationError

### `use_cases/` — Business Logic

One class per action, all async:

| Subdirectory | Use Cases |
|---|---|
| `auth/` | RegisterUserUseCase, LoginUserUseCase, RefreshTokenUseCase, LogoutUserUseCase |
| `channels/` | CreateChannelUseCase, JoinChannelUseCase, LeaveChannelUseCase, GetChannelUseCase, ListChannelsUseCase, ListMembersUseCase, UpdateChannelUseCase, DeleteChannelUseCase |
| `messaging/` | SendMessageUseCase, EditMessageUseCase, DeleteMessageUseCase, GetMessageHistoryUseCase, MarkAsReadUseCase, GetUnreadCountUseCase |
| `direct_messages/` | SendDirectMessageUseCase, GetDMHistoryUseCase, CreateConversationUseCase, ListConversationsUseCase |
| `threads/` | CreateThreadUseCase, ReplyToThreadUseCase, GetThreadRepliesUseCase |
| `files/` | UploadFileUseCase |
| `mentions/` | ParseMentionsUseCase, ListUserMentionsUseCase |
| `reactions/` | AddReactionUseCase, RemoveReactionUseCase, ListReactionsUseCase |
| `notifications/` | SendNotificationUseCase, ListNotificationsUseCase, MarkNotificationReadUseCase, MarkAllReadUseCase |
| `presence/` | UpdatePresenceUseCase, GetOnlineUsersUseCase |
| `search/` | SearchMessagesUseCase, SearchChannelsUseCase |
| `users/` | GetUserProfileUseCase, UpdateUserProfileUseCase |

All use cases: inject repository abstractions, execute async validation, raise domain exceptions.

### `adapters/` — External Integrations

#### `api/` — HTTP FastAPI Layer
- `routes/{resource}_routes.py` — Endpoint handlers
  - `auth_routes.py` — POST /auth/register, /auth/login, /auth/refresh, /auth/logout
  - `channel_routes.py` — CRUD channels, join, leave, members
  - `message_routes.py` — Send, edit, delete, history
  - `thread_routes.py` — Create thread, reply, get replies
  - `dm_routes.py` — Send DM, history, conversations
  - `file_routes.py` — Upload file
  - `user_routes.py` — Profile, update
  - `mention_routes.py` — List mentions
  - `reaction_routes.py` — Add, remove reactions
  - `notification_routes.py` — List, mark read
  - `search_routes.py` — Search messages, channels

- `schemas/` — Pydantic request/response models (one per resource)
  - `auth_schemas.py` — RegisterRequest, LoginRequest, TokenResponse
  - `user_schemas.py` — UserProfileResponse, UpdateProfileRequest
  - (+ schemas for channels, messages, threads, DMs, files, etc.)

- `middleware/` — Auth, CORS, error handling
- `jwt_token_service.py` — TokenService impl (JWT creation/validation, HS256)
- `bcrypt_password_service.py` — PasswordService impl (bcrypt hash/verify)

#### `persistence/` — Database Layer
- `database.py` — AsyncSession factory, connection management
- `models/` — SQLAlchemy ORM models (mirror entities)
  - `user_model.py` — Mapped to `users` table
  - `channel_model.py` — Mapped to `channels` table
  - `message_model.py` — Mapped to `messages` table
  - (+ models for threads, DMs, files, reactions, notifications)
  - Each model: `to_entity()` → domain entity, `from_entity()` ← domain entity

- `repositories/` — Concrete repository implementations
  - `sqlalchemy_user_repository.py` — 75 lines, async CRUD
  - `sqlalchemy_channel_repository.py` — Channel persistence
  - `sqlalchemy_message_repository.py` — Message persistence
  - (+ repositories for threads, DMs, files, reactions, notifications)

#### `websocket/` — Socket.IO Real-time
- `event_handlers/` — WebSocket message handlers
  - `message_handlers.py` — Emit `message_created`, `message_edited`, `message_deleted`
  - `presence_handlers.py` — Emit `user_joined`, `user_left`, `presence_updated`
  - `typing_handlers.py` — Emit `user_typing`

#### `redis/` — Cache & Pub-Sub
- Session caching, rate limiting, pub-sub for cross-worker messaging

#### `celery_tasks/` — Async Tasks
- `notification_tasks.py` — Send mention/DM notifications
- `file_processing_tasks.py` — Generate thumbnails, compress uploads
- `cleanup_tasks.py` — Archive old messages, delete expired tokens

#### `storage/` — File Storage
- `local_file_storage.py` — Write/read uploaded files to disk

### `infrastructure/` — Framework Configuration

- `config.py` — Settings class (pydantic-settings) with env variables
  - Database URL, Redis URL, JWT secret, upload directory, etc.
- `container.py` — Dependency injection setup (repositories, use cases, etc.)
- `celery_app.py` — Celery worker configuration (Redis broker)
- `logging_config.py` — Structured logging (JSON format for prod)
- `main.py` — FastAPI app factory, exception handlers, route registration

### Entry Point

- `main.py` — `create_app() → FastAPI` factory function
  - Exception handlers for all domain errors (map to HTTP status codes)
  - Routes registered: auth, channels, messages, threads, DMs, files, users, mentions, reactions, notifications, search
  - CORS middleware, logging middleware, auth middleware

## Tests Structure (`tests/`)

### Test Levels

| Level | Location | Purpose | Count |
|---|---|---|---|
| **Unit** | `tests/unit/` | Domain entities, use cases (no external deps) | ~200 |
| **Integration** | `tests/integration/` | Repositories, adapters against real PostgreSQL | ~100 |
| **E2E** | `tests/e2e/` | Full HTTP request → response journeys | ~50 |
| **Performance** | `tests/performance/` | Benchmarks, stress tests | ~10 |

### Directory Layout

```
tests/
├── unit/
│   ├── domain/                  # Entity, exception tests
│   ├── use_cases/               # Business logic tests (all use case subdirs mirrored)
│   │   ├── auth/
│   │   ├── channels/
│   │   ├── messaging/
│   │   └── ...
│   ├── adapters/
│   │   └── api/                 # Schema, JWT, password utility tests
│   └── infrastructure/          # Config, DI container tests
├── integration/
│   └── adapters/                # Repository, API endpoint tests against real DB
├── e2e/                         # Full user journey tests
├── fakes/                       # In-memory mock implementations
│   ├── fake_repositories.py     # FakeUserRepository, FakeChannelRepository, etc.
│   ├── fake_redis.py            # In-memory Redis
│   └── fake_email_service.py    # Mock email sender
├── conftest.py                  # Global pytest fixtures
│   - async_client (FastAPI test client)
│   - session (AsyncSession for tests)
│   - sample_user, sample_channel (factory helpers)
└── factories.py                 # factory_boy generators for test data
```

### Test Coverage

```
Total: 377 tests
Coverage: 92.03% (target: 90%)
All tests async using pytest-asyncio
```

## Docker Setup

```
docker/
├── Dockerfile                   # Python 3.11-slim base, installs deps
├── docker-compose.yml           # Services: app, postgres, redis, celery worker
├── docker-compose.test.yml      # Overlay for test runs
└── .dockerignore                # Exclude .git, __pycache__, etc.
```

**Key services:**
- **app**: FastAPI server on port 8000
- **db**: PostgreSQL 15 on port 5432 (user: `chat`, db: `chat`)
- **redis**: Redis 7 on port 6379 (databases 0, 1, 2 for cache, broker, backend)
- **celery-worker**: Celery worker consuming tasks from Redis

## Database Migrations

```
alembic/
├── versions/                    # Migration files (auto-generated by alembic)
├── env.py                       # Migration runner config
└── script.py.mako               # Migration template
```

Run: `alembic upgrade head` to apply all pending migrations.

## Configuration Files

- `pyproject.toml` — Project metadata, dependencies, dev dependencies, pytest config, ruff linter config, coverage config
- `.env.example` — Environment variable template (copy to `.env` for local dev)
- `.gitignore` — Exclude `.venv/`, `.env`, `__pycache__/`, `.coverage`, etc.
- `alembic.ini` — Alembic configuration

## Key Metrics

| Metric | Value |
|--------|-------|
| Python Version | 3.11 |
| Total Tests | 377 |
| Code Coverage | 92.03% |
| Lines of Code (src/) | ~2,300 |
| Max File Size | 200 lines (enforced) |
| Async-First | Yes (all I/O async) |
| Type Hints | Mandatory |

## How to Get Started

1. **Install deps**: `pip install -e ".[dev]"`
2. **Start services**: `cd docker && docker-compose up --build`
3. **Run tests**: `pytest --cov=src`
4. **View API docs**: http://localhost:8000/docs
5. **Check coverage**: Coverage report auto-printed by pytest, min 90%

## Code Quality

- **Linting**: Ruff (line-length 120, strict F/E/I/N/W rules)
- **Type hints**: Mandatory on all functions
- **Testing**: TDD (write tests before code)
- **Architecture**: Clean (domain → use cases → adapters → framework)
- **Async design**: All I/O operations use `async/await`
