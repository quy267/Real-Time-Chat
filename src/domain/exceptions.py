"""Domain-level exceptions used across all layers."""


class DomainError(Exception):
    """Base exception for domain errors."""

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""


class DuplicateEntityError(DomainError):
    """Raised when creating an entity that already exists."""


class ValidationError(DomainError):
    """Raised when entity data fails validation."""


class AuthenticationError(DomainError):
    """Raised when authentication fails."""


class AuthorizationError(DomainError):
    """Raised when a user lacks permission for an action."""
