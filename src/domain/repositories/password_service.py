"""Abstract PasswordService — domain interface for password hashing and verification."""

from abc import ABC, abstractmethod


class PasswordService(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Return a secure hash of the given plain-text password."""

    @abstractmethod
    def verify_password(self, plain: str, hashed: str) -> bool:
        """Return True if plain matches the hashed password."""
