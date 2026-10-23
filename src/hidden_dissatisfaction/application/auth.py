from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from hidden_dissatisfaction.domain.auth import (
    AccessToken,
    InvalidCredentials,
    InvalidToken,
    User,
    UserNotFound,
)


class UserRepository(Protocol):
    async def by_email(self, email: str) -> User | None: ...
    async def by_id(self, user_id: UUID) -> User | None: ...


class AuthService:
    def __init__(
        self, users: UserRepository, secret: str, algorithm: str = "HS256", minutes: int = 30
    ) -> None:
        self.users, self.secret, self.algorithm, self.minutes = users, secret, algorithm, minutes
        self.passwords = PasswordHash.recommended()

    async def login(self, email: str, password: str) -> AccessToken:
        user = await self.users.by_email(email)
        if (
            not user
            or not user.is_active
            or not self.passwords.verify(password, user.password_hash)
        ):
            raise InvalidCredentials
        expires = datetime.now(UTC) + timedelta(minutes=self.minutes)
        return AccessToken(
            jwt.encode(
                {"sub": str(user.id), "exp": expires}, self.secret, algorithm=self.algorithm
            ),
            expires,
        )

    async def identify(self, token: str) -> User:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidToken from exc
        user = await self.users.by_id(UUID(str(payload["sub"])))
        if not user or not user.is_active:
            raise UserNotFound
        return user
