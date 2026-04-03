"""MessageContent value object — validated chat message string."""

from src.domain.exceptions import ValidationError

MAX_CONTENT_LENGTH = 4000


class MessageContent:
    """Immutable value object wrapping a validated message string."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        stripped = value.strip()
        if not stripped:
            raise ValidationError("Message content must not be empty.")
        if len(value) > MAX_CONTENT_LENGTH:
            raise ValidationError(
                f"Message content must not exceed {MAX_CONTENT_LENGTH} characters."
            )
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"MessageContent({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MessageContent):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)
