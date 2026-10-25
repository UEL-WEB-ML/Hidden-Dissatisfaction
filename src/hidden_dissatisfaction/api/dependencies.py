"""Production dependency wiring for HTTP interfaces."""

from hidden_dissatisfaction.application.auth import AuthService
from hidden_dissatisfaction.application.parameters import CreateParameterVersion
from hidden_dissatisfaction.infrastructure.database import build_session_factory
from hidden_dissatisfaction.infrastructure.postgres_claim_case import PostgresClaimCase
from hidden_dissatisfaction.infrastructure.postgres_operational_reads import (
    PostgresOperationalReadModel,
)
from hidden_dissatisfaction.infrastructure.postgres_parameters import PostgresParameterVersionWriter
from hidden_dissatisfaction.infrastructure.postgres_risk_queue import PostgresRiskOrderQuery
from hidden_dissatisfaction.infrastructure.postgres_users import PostgresUserRepository

from .config import Settings


def build_auth_service(settings: Settings) -> AuthService:
    """Build the production authentication service from settings and adapters."""
    users = PostgresUserRepository(build_session_factory(settings.database_url))
    return AuthService(
        users=users,
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        minutes=settings.access_token_minutes,
    )


def build_parameter_version_service(settings: Settings) -> CreateParameterVersion:
    """Build the parameter write use case from the production Postgres adapter."""
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return CreateParameterVersion(PostgresParameterVersionWriter(dsn))


def build_risk_order_query(settings: Settings) -> PostgresRiskOrderQuery:
    """Build the read-only Queue adapter from the application database URL."""
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return PostgresRiskOrderQuery(dsn)


def build_operational_reads(settings: Settings) -> PostgresOperationalReadModel:
    """Build the read-only P9.1 operational projections."""
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return PostgresOperationalReadModel(dsn)


def build_claim_case(settings: Settings) -> PostgresClaimCase:
    """Build the transactional P9 claim adapter."""
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return PostgresClaimCase(dsn)
