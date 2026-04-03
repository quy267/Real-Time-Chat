"""Abstract TokenService — domain interface for JWT token creation and decoding."""

from abc import ABC, abstractmethod

from src.domain.value_objects.token_pair import TokenPair


class TokenService(ABC):
    @abstractmethod
    def create_token_pair(self, user_id: str) -> TokenPair:
        """Create an access + refresh token pair for the given user_id."""

    @abstractmethod
    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT. Raises an exception on failure."""

    @abstractmethod
    def create_access_token(self, user_id: str) -> str:
        """Create a short-lived access token."""

    @abstractmethod
    def create_refresh_token(self, user_id: str) -> str:
        """Create a long-lived refresh token."""
