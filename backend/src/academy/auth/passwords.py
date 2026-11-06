"""Argon2id password hashing. Passwords are 12–128 characters (initial value, review D4)."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

MIN_LENGTH = 12
MAX_LENGTH = 128

_hasher = PasswordHasher()  # argon2id with library defaults (RFC 9106 recommended profile)
#: Used to equalize timing when the account does not exist.
_DUMMY_HASH = _hasher.hash("timing-equalizer-not-a-password")


class PasswordPolicyError(ValueError):
    pass


def check_policy(password: str) -> None:
    if not MIN_LENGTH <= len(password) <= MAX_LENGTH:
        raise PasswordPolicyError(f"password must be {MIN_LENGTH}–{MAX_LENGTH} characters")


def hash_password(password: str) -> str:
    check_policy(password)
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """Constant-work verification; ``password_hash=None`` verifies against a dummy hash."""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
