from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    """Roles supported by the operational workflow."""

    SPECIALIST = "SPECIALIST"
    MANAGER = "MANAGER"


@dataclass(frozen=True)
class User:
    id: UUID
    username: str
    password_hash: str
    is_active: bool = True
    preferred_language: str | None = None
    full_name: str = ""
    role: Role = Role.SPECIALIST
    created_at: datetime | None = None


@dataclass(frozen=True)
class AccessToken:
    token: str
    expires_at: datetime


class AuthError(Exception):
    pass


class InvalidCredentials(AuthError):
    pass


class InvalidToken(AuthError):
    pass


class UserNotFound(AuthError):
    pass
