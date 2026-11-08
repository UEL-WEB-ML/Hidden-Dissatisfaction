"""PostgreSQL adapter for the authentication user port."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hidden_dissatisfaction.domain.auth import Role, User


class PostgresUserRepository:
    """Map the minimal auth projection from ``app.users`` to domain users."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    @staticmethod
    def _to_user(mapping: RowMapping) -> User:
        return User(
            id=mapping["user_id"],
            username=mapping["username"],
            password_hash=mapping["password_hash"],
            is_active=mapping["is_active"],
            preferred_language=mapping["preferred_language"],
            full_name=mapping["full_name"],
            role=Role(mapping["role"]),
            created_at=mapping["created_at"],
        )

    async def by_username(self, username: str) -> User | None:
        statement = text(
            """
            SELECT user_id, username, password_hash, is_active, preferred_language,
                   full_name, role, created_at
            FROM app.users
            WHERE username = :username
            """
        )
        async with self._sessions() as session:
            row = (await session.execute(statement, {"username": username})).one_or_none()
        return self._to_user(row._mapping) if row is not None else None

    async def by_id(self, user_id: UUID) -> User | None:
        statement = text(
            """
            SELECT user_id, username, password_hash, is_active, preferred_language,
                   full_name, role, created_at
            FROM app.users
            WHERE user_id = :user_id
            """
        )
        async with self._sessions() as session:
            row = (await session.execute(statement, {"user_id": user_id})).one_or_none()
        return self._to_user(row._mapping) if row is not None else None

    async def set_preferred_language(self, user_id: UUID, language: str) -> User:
        statement = text(
            """
            UPDATE app.users
            SET preferred_language = :language
            WHERE user_id = :user_id AND is_active
            RETURNING user_id, username, password_hash, is_active, preferred_language,
                      full_name, role, created_at
            """
        )
        async with self._sessions.begin() as session:
            row = (
                await session.execute(statement, {"user_id": user_id, "language": language})
            ).one_or_none()
        if row is None:
            raise LookupError("active user not found")
        return self._to_user(row._mapping)
