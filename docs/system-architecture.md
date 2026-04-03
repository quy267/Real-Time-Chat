# System Architecture

## Layered Clean Architecture

The codebase is organized into four interdependent layers with strict dependency flow: inner layers never know about outer layers.

```
┌─────────────────────────────────────────────────────┐
│ Frameworks & Drivers Layer                          │
│ (FastAPI app, DB, Redis, WebSocket, Celery)        │
├─────────────────────────────────────────────────────┤
│ Interface Adapters Layer                            │
│ (API routes, repositories, schemas, middleware)    │
├─────────────────────────────────────────────────────┤
│ Use Cases Layer                                     │
│ (Business logic, one class per action)             │
├─────────────────────────────────────────────────────┤
│ Domain Layer (Entities)                             │
│ (Pure Python, framework-agnostic)                  │
└─────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/
├── domain/                      # Layer 1: Core business rules
│   ├── entities/                # Dataclass entities (User, Message, Channel, etc.)
│   ├── value_objects/           # Immutable domain concepts (TokenPair, PresenceStatus)
│   ├── repositories/            # Abstract repository interfaces (ABC)
│   │   ├── *_repository.py      # Domain entity persistence abstractions
│   │   ├── token_service.py     # TokenService ABC (JWT creation/validation)
│   │   └── password_service.py  # PasswordService ABC (hash/verify passwords)
│   └── exceptions.py            # Domain-level errors
│
├── use_cases/                   # Layer 2: Business logic
│   ├── auth/                    # register_user.py, login_user.py, refresh_token.py
│   ├── channels/                # create_channel.py, join_channel.py, list_members.py
│   ├── messaging/               # send_message.py, edit_message.py, get_message_history.py
│   ├── direct_messages/         # send_direct_message.py, get_dm_history.py
│   ├── threads/                 # create_thread.py, reply_to_thread.py
│   ├── files/                   # upload_file.py
│   ├── mentions/                # parse_mentions.py, list_user_mentions.py
│   ├── reactions/               # add_reaction.py, remove_reaction.py
│   ├── notifications/           # send_notification.py, list_notifications.py
│   ├── presence/                # update_presence.py, get_online_users.py
│   └── search/                  # search_messages.py, search_channels.py
│
├── adapters/                    # Layer 3: External interface implementations
│   ├── api/                     # FastAPI HTTP layer
│   │   ├── routes/              # Endpoint handlers (auth_routes.py, channel_routes.py, etc.)
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── middleware/          # Auth middleware, CORS, logging
│   │   ├── jwt_token_service.py # TokenService implementation (JWT tokens)
│   │   ├── bcrypt_password_service.py # PasswordService implementation (bcrypt hashing)
│   ├── persistence/             # Database layer
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── repositories/        # Concrete repository implementations
│   │   └── database.py          # Session management, migrations
│   ├── websocket/               # Socket.IO real-time events
│   │   └── event_handlers/      # WebSocket message handlers
│   ├── redis/                   # Redis cache/pub-sub
│   ├── celery_tasks/            # Async task definitions
│   └── storage/                 # File storage adapter
│
└── infrastructure/              # Layer 4: Framework configuration
    ├── config.py                # Environment settings (Settings class)
    ├── container.py             # Dependency injection setup
    ├── celery_app.py            # Celery worker configuration
    ├── logging_config.py        # Structured logging setup
    └── main.py                  # FastAPI app factory, exception handlers
```

## Data Flow Example: Send Message

```
1. Client: POST /api/channels/{channel_id}/messages
   ↓
2. API Layer (message_routes.py)
   - Validates JWT token (middleware)
   - Deserializes JSON to SendMessageRequest (Pydantic schema)
   ↓
3. Use Case (send_message.py)
   - Validates user membership in channel
   - Validates message content (non-empty, max length)
   - Creates Message entity
   - Persists via repository abstraction
   ↓
4. Adapter (sqlalchemy_message_repository.py)
   - Converts Message entity → MessageModel (SQLAlchemy)
   - Executes INSERT query via AsyncSession
   ↓
5. Framework (PostgreSQL)
   - Stores message with metadata (created_at, user_id, etc.)
   ↓
6. Real-time (WebSocket event handler)
   - Publishes message_created event via Socket.IO
   - Broadcasts to all channel members
   ↓
7. Response: MessageResponse (Pydantic schema) serialized to JSON
```

## Key Architectural Patterns

### Repository Pattern (Dependency Inversion)

Use cases depend on **abstract repositories** (ABC), not concrete implementations:

```python
# domain/repositories/message_repository.py (abstract)
class MessageRepository(ABC):
    @abstractmethod
    async def create(self, message: Message) -> Message: ...

# adapters/persistence/repositories/sqlalchemy_message_repository.py (concrete)
class SQLAlchemyMessageRepository(MessageRepository):
    async def create(self, message: Message) -> Message:
        model = MessageModel.from_entity(message)
        self._session.add(model)
        await self._session.flush()
        return model.to_entity()
```

### Cross-Cutting Services (TokenService & PasswordService)

Auth use cases depend on abstract service interfaces defined in the domain layer:

```python
# domain/repositories/token_service.py (abstract)
class TokenService(ABC):
    @abstractmethod
    def create_token_pair(self, user_id: str) -> TokenPair: ...
    @abstractmethod
    def decode_token(self, token: str) -> dict: ...

# adapters/api/jwt_token_service.py (concrete)
class JWTTokenService(TokenService):
    def create_token_pair(self, user_id: str) -> TokenPair:
        access = self._create_access_token(user_id)
        refresh = self._create_refresh_token(user_id)
        return TokenPair(access_token=access, refresh_token=refresh)
```

This pattern ensures:
- Auth use cases accept `TokenService` and `PasswordService` via constructor injection
- Inner layers (domain) never import outer layers (adapters)
- Easy to test with mock services
- Easy to swap implementations (e.g., OAuth, HSM-based tokens)

### One Use Case Per Class

Each action has exactly one `execute()` method:

```python
# Separate classes for clarity and testability
class SendMessageUseCase: async def execute(self, ...) -> Message: ...
class EditMessageUseCase: async def execute(self, ...) -> Message: ...
class DeleteMessageUseCase: async def execute(self, ...) -> None: ...
```

### Entity-to-Model Conversion

Domain entities (pure Python dataclasses) are converted to ORM models at the adapter layer:

```python
# Domain entity
@dataclass
class Message:
    id: UUID
    content: str
    created_at: datetime

# SQLAlchemy model
class MessageModel(Base):
    def to_entity(self) -> Message:
        return Message(id=self.id, content=self.content, created_at=self.created_at)

    @classmethod
    def from_entity(cls, entity: Message) -> MessageModel:
        return cls(id=entity.id, content=entity.content, created_at=entity.created_at)
```

### Async-First Design

All I/O operations (database, Redis, file uploads) use `async/await`:

```python
async def execute(self, user_id: UUID, channel_id: UUID) -> Channel:
    user = await self._user_repo.get_by_id(user_id)
    channel = await self._channel_repo.get_by_id(channel_id)
    await self._channel_repo.add_member(channel_id, user_id)
```

## Database Schema

PostgreSQL with Alembic migrations in `alembic/versions/`. Key tables:

- `users` — User accounts with email, password_hash, status
- `channels` — Public/private channels
- `channel_members` — Many-to-many membership tracking
- `messages` — Messages in channels with content, edited_at
- `threads` — Message replies (child messages)
- `direct_messages` — Peer-to-peer conversations
- `reactions` — Emoji reactions to messages
- `files` — Uploaded file metadata
- `notifications` — User notifications with read status

## Real-time Events (Socket.IO)

WebSocket handlers in `adapters/websocket/event_handlers/` emit events:

- `message_created` — New message in channel
- `message_edited` — Message content updated
- `message_deleted` — Message removed
- `user_joined` — User entered channel
- `user_left` — User left channel
- `user_typing` — User is typing indicator
- `presence_updated` — User online/offline status

## Async Task Queue (Celery)

Background jobs in `adapters/celery_tasks/`:

- **Notifications** — Send mention/DM notifications
- **File Processing** — Generate thumbnails, compress uploads
- **Cleanup** — Archive old messages, delete expired tokens

## Testing Strategy

```
tests/
├── unit/                        # Fast, isolated tests
│   ├── domain/                  # Entity validation, exceptions
│   └── use_cases/               # Business logic, happy + error paths
├── integration/                 # Real services (DB, Redis)
│   └── adapters/                # Repository, API endpoint tests
├── e2e/                         # Full user journeys
├── fakes/                       # In-memory mock implementations
└── conftest.py                  # Pytest fixtures (async DB, containers)
```

All async tests use `pytest-asyncio` with `asyncio_mode = "auto"`.
