"""Password hashing and verification using bcrypt directly.

Using bcrypt>=4.x directly because passlib is not compatible with bcrypt 4+
(it relies on bcrypt.__about__ which was removed in 4.0).

NOTE: bcrypt is CPU-bound (~250ms). For high-traffic auth endpoints,
wrap in asyncio.to_thread() at the call site.
"""

import bcrypt

_ROUNDS = 12


def hash_password(password: str) -> str:
    """Return bcrypt hash of the given plain-text password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
