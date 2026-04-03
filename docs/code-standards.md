# Code Standards & Conventions

## File Naming

- **Python modules**: `snake_case.py` (e.g., `send_message.py`, `user_repository.py`)
- **Classes**: `PascalCase` (e.g., `SendMessageUseCase`, `UserRepository`)
- **Functions/variables**: `snake_case` (e.g., `execute()`, `user_id`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_MESSAGE_LENGTH`)

## Type Hints & Async

**Mandatory type hints** on all functions:

```python
async def send_message(
    user_id: UUID,
    channel_id: UUID,
    content: str,
) -> Message:
    """Send a message to a channel."""
    ...
```

**Async-first design** for all I/O:
- Database queries: `async def` with `await`
- Redis operations: `async def` with `await`
- File uploads: `async def` with `await`
- Never use sync blocking calls in endpoints

## Domain Layer (Entities & Value Objects)

**Entities** are dataclasses with no framework imports:

```python
# src/domain/entities/message.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

@dataclass
class Message:
    id: UUID
    channel_id: UUID
    user_id: UUID
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_deleted: bool = False
```

**No FastAPI, SQLAlchemy, or Pydantic** in domain entities — keep them pure Python.

**Value Objects** are immutable, represent domain concepts:

```python
# src/domain/value_objects/token_pair.py
from dataclasses import dataclass

@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
```

## Repository Interfaces

**Abstract repositories** in domain layer:

```python
# src/domain/repositories/message_repository.py
from abc import ABC, abstractmethod
from uuid import UUID

class MessageRepository(ABC):
    @abstractmethod
    async def create(self, message: Message) -> Message:
        """Persist and return message."""

    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Message | None:
        """Return message or None."""

    @abstractmethod
    async def update(self, message: Message) -> Message:
        """Persist updates and return updated entity."""
```

**Concrete implementations** in adapter layer (SQLAlchemy, Redis, etc.):

```python
# src/adapters/persistence/repositories/sqlalchemy_message_repository.py
class SQLAlchemyMessageRepository(MessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, message: Message) -> Message:
        model = MessageModel.from_entity(message)
        self._session.add(model)
        await self._session.flush()
        return model.to_entity()
```

## Use Cases

**One class per action**, named `{Action}{Noun}UseCase`:

```python
# src/use_cases/messaging/send_message.py
class SendMessageUseCase:
    def __init__(
        self,
        message_repo: MessageRepository,
        channel_repo: ChannelRepository,
        user_repo: UserRepository,
    ) -> None:
        self._message_repo = message_repo
        self._channel_repo = channel_repo
        self._user_repo = user_repo

    async def execute(
        self,
        user_id: UUID,
        channel_id: UUID,
        content: str,
    ) -> Message:
        """Send a message to a channel."""
        # Validate inputs
        # Check permissions
        # Create entity
        # Persist via repository
        return message
```

**Single public method** (`execute()`) — all logic inside.

**Raise domain exceptions** for error cases:

```python
from src.domain.exceptions import EntityNotFoundError, ValidationError

class SendMessageUseCase:
    async def execute(self, user_id: UUID, channel_id: UUID, content: str) -> Message:
        channel = await self._channel_repo.get_by_id(channel_id)
        if not channel:
            raise EntityNotFoundError(f"Channel {channel_id} not found")
        
        if not content.strip():
            raise ValidationError("Message content cannot be empty")
        
        # ... rest of logic
```

## Pydantic Schemas

**Request/response models** in adapter layer:

```python
# src/adapters/api/schemas/message_schemas.py
from pydantic import BaseModel, Field
from datetime import datetime

class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)

class MessageResponse(BaseModel):
    id: str
    channel_id: str
    user_id: str
    content: str
    created_at: str
    updated_at: str | None
    is_deleted: bool
```

**Never mix Pydantic models with domain entities** — convert at API boundary.

## API Routes

**Organize by resource** in `src/adapters/api/routes/{resource}_routes.py`:

```python
# src/adapters/api/routes/message_routes.py
from fastapi import APIRouter, Depends, HTTPException
from src.adapters.api.schemas.message_schemas import SendMessageRequest, MessageResponse

router = APIRouter(prefix="/channels/{channel_id}/messages", tags=["messages"])

@router.post("", response_model=MessageResponse)
async def send_message(
    channel_id: str,
    req: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
    send_message_uc: SendMessageUseCase = Depends(get_send_message_uc),
) -> MessageResponse:
    """Send a message to a channel."""
    try:
        message = await send_message_uc.execute(
            user_id=UUID(user_id),
            channel_id=UUID(channel_id),
            content=req.content,
        )
        return MessageResponse(
            id=str(message.id),
            channel_id=str(message.channel_id),
            user_id=str(message.user_id),
            content=message.content,
            created_at=message.created_at.isoformat(),
            updated_at=message.updated_at.isoformat() if message.updated_at else None,
            is_deleted=message.is_deleted,
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
```

## Testing Strategy (TDD)

**Write tests before code.** Three test levels:

### 1. Unit Tests (Domain & Use Cases)

```python
# tests/unit/use_cases/messaging/test_send_message.py
import pytest
from uuid import uuid4
from src.use_cases.messaging.send_message import SendMessageUseCase
from src.domain.exceptions import EntityNotFoundError, ValidationError
from tests.fakes.fake_repositories import FakeMessageRepository, FakeChannelRepository

@pytest.mark.asyncio
class TestSendMessageUseCase:
    async def test_send_message_success(self):
        # Arrange
        message_repo = FakeMessageRepository()
        channel_repo = FakeChannelRepository()
        uc = SendMessageUseCase(message_repo, channel_repo)
        user_id, channel_id = uuid4(), uuid4()
        
        # Act
        result = await uc.execute(user_id, channel_id, "Hello")
        
        # Assert
        assert result.content == "Hello"
        assert result.user_id == user_id

    async def test_send_empty_message_raises(self):
        # Arrange
        uc = SendMessageUseCase(...)
        
        # Act & Assert
        with pytest.raises(ValidationError, match="cannot be empty"):
            await uc.execute(uuid4(), uuid4(), "")
```

### 2. Integration Tests (Adapters)

Test against real PostgreSQL, Redis in Docker:

```python
# tests/integration/adapters/test_sqlalchemy_message_repository.py
@pytest.mark.asyncio
class TestSQLAlchemyMessageRepository:
    async def test_create_message_persists_to_db(self, session: AsyncSession):
        # Arrange
        repo = SQLAlchemyMessageRepository(session)
        message = Message(id=uuid4(), ...)
        
        # Act
        result = await repo.create(message)
        
        # Assert
        saved = await repo.get_by_id(result.id)
        assert saved.content == message.content
```

### 3. End-to-End Tests

Full HTTP request → response cycle:

```python
# tests/e2e/test_send_message_flow.py
@pytest.mark.asyncio
class TestSendMessageFlow:
    async def test_user_can_send_message_to_channel(
        self,
        client: AsyncClient,
        user_token: str,
        channel_id: str,
    ):
        # Arrange
        headers = {"Authorization": f"Bearer {user_token}"}
        payload = {"content": "Hello world"}
        
        # Act
        response = await client.post(
            f"/api/channels/{channel_id}/messages",
            json=payload,
            headers=headers,
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["content"] == "Hello world"
```

## File Size Limit

**Keep individual Python files under 200 lines** (excluding imports, docstrings):

- Use case class: ~50 lines
- Repository implementation: ~70 lines
- API route handler: ~100 lines

If a file exceeds 200 lines, **split into focused modules**.

## Exception Handling

**Domain exceptions** (no HTTP details):

```python
# src/domain/exceptions.py
class DomainError(Exception):
    def __init__(self, message: str = ""):
        self.message = message

class EntityNotFoundError(DomainError): ...
class DuplicateEntityError(DomainError): ...
class ValidationError(DomainError): ...
class AuthenticationError(DomainError): ...
class AuthorizationError(DomainError): ...
```

**Map to HTTP** in routes only:

```python
try:
    result = await use_case.execute(...)
except EntityNotFoundError as e:
    raise HTTPException(status_code=404, detail=e.message)
except DuplicateEntityError as e:
    raise HTTPException(status_code=409, detail=e.message)
except ValidationError as e:
    raise HTTPException(status_code=422, detail=e.message)
```

## Imports

**Absolute imports only**, no relative:

```python
# Good
from src.domain.entities.user import User
from src.use_cases.auth.register_user import RegisterUserUseCase

# Bad
from ..domain.entities.user import User
from .register_user import RegisterUserUseCase
```

**Import order** (PEP 8):
1. Standard library (`datetime`, `uuid`, `json`)
2. Third-party (`fastapi`, `sqlalchemy`, `pydantic`)
3. Local project (`src.domain`, `src.adapters`)

## Logging

Use structured logging via `logging` module:

```python
import logging

logger = logging.getLogger(__name__)

class SendMessageUseCase:
    async def execute(self, user_id: UUID, channel_id: UUID, content: str) -> Message:
        logger.info("Sending message", extra={"user_id": str(user_id), "channel_id": str(channel_id)})
        try:
            message = await self._message_repo.create(...)
            logger.info("Message sent successfully", extra={"message_id": str(message.id)})
            return message
        except Exception as e:
            logger.error("Failed to send message", exc_info=True)
            raise
```

## Repository Write Operations

**All SQLAlchemy repository write methods must call `commit()` after persisting:**

```python
class SQLAlchemyUserRepository(UserRepository):
    async def create(self, user: User) -> User:
        model = UserModel.from_entity(user)
        self._session.add(model)
        await self._session.commit()  # ← REQUIRED
        return model.to_entity()
    
    async def update(self, user: User) -> User:
        # ... merge and update model ...
        await self._session.commit()  # ← REQUIRED
        return model.to_entity()
```

This ensures data is durably persisted to the database.

## Security Standards

### JWT Secret Management

JWT secret must be configured via `CHAT_JWT_SECRET` environment variable:
- **Production** (`CHAT_DEBUG=false`): App startup fails if secret is not set or is the default value
- **Development** (`CHAT_DEBUG=true`): Default secret allowed for local testing

```python
if not self.debug and self.jwt_secret == "default-secret":
    raise ValueError("JWT secret not configured for production")
```

### Socket.IO Error Handling

WebSocket error handlers must NOT leak exception details to clients:

```python
@sio.on_error()
async def error_handler(e):
    # Bad: return str(e)  # Exposes internal implementation details
    # Good:
    logger.error("Socket.IO error", exc_info=True)  # Log server-side
    return {"error": "Internal server error"}  # Generic client response
```

### Allowed Content Types

SVG uploads are **blocked** (XSS vector). Only safe content types allowed:
- Images: `image/jpeg`, `image/png`, `image/gif`
- Documents: `application/pdf`, `text/plain`
- Archives: `application/zip`

### Authorization Enforcement

Channel membership operations enforce authorization at the use case level:
- Users can only remove themselves from channels (not others)
- Channel deletion restricted to channel creator
- All endpoints verify user_id matches authenticated token

## File Upload Best Practices

Disk I/O in file uploads uses `asyncio.to_thread()` for non-blocking operations:

```python
async def execute(self, user_id: UUID, file_data: bytes, filename: str) -> File:
    # Write to disk without blocking event loop
    await asyncio.to_thread(
        self._storage.write_file,
        filename,
        file_data
    )
    # ... create File entity and persist ...
```

## Code Coverage

Minimum **90% coverage** enforced by pytest:

```bash
pytest --cov=src --cov-report=term-missing
```

Current: **92.03%** (377 tests)
