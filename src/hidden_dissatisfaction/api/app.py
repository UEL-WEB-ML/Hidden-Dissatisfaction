from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any, Protocol

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from hidden_dissatisfaction.application.claim import ClaimCase
from hidden_dissatisfaction.application.parameters import (
    CreateParameterVersionCommand,
    ParameterVersion,
)
from hidden_dissatisfaction.application.queue import (
    QueuePage as ApplicationQueuePage,
)
from hidden_dissatisfaction.application.queue import (
    RiskOrderQueryPort,
    summarize_queue,
)
from hidden_dissatisfaction.application.workflow_commands import WorkflowCommands
from hidden_dissatisfaction.domain.auth import (
    AccessToken,
    InvalidCredentials,
    InvalidToken,
    Role,
    User,
    UserNotFound,
)
from hidden_dissatisfaction.domain.parameters import ParameterValidationError
from hidden_dissatisfaction.domain.queue import QueueFilters, QueueQueryValidationError
from hidden_dissatisfaction.domain.workflow import WorkflowPolicyError
from hidden_dissatisfaction.infrastructure.postgres_claim_case import (
    ClaimConflictError,
    ClaimNotFoundError,
)

from .authorization import require_manager
from .config import Settings
from .dependencies import (
    build_auth_service,
    build_case_reads,
    build_claim_case,
    build_evidence_store,
    build_operational_reads,
    build_parameter_version_service,
    build_risk_order_query,
    build_workflow_commands,
)
from .schemas import (
    ClaimResponse,
    CreateParameterVersionRequest,
    LoginRequest,
    ParameterVersionResponse,
    Principal,
    QueueOrder,
    QueueSummary,
    TokenResponse,
    UpdateMeRequest,
    UserResponse,
)
from .schemas import (
    QueuePage as PublicQueuePage,
)
from .workflow_routes import CaseReads, EvidenceFiles, build_workflow_router


async def readiness_check() -> bool:
    """Check configured PostgreSQL connectivity and migration state when applicable."""
    import os

    dsn = os.getenv("HD_DATABASE_URL", "")
    if not dsn.startswith(("postgres://", "postgresql://", "postgresql+asyncpg://")):
        return False
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = "postgresql://" + dsn.removeprefix("postgresql+asyncpg://")
    try:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(dsn, connect_timeout=2, row_factory=dict_row) as connection:
            row = connection.execute(
                """
                SELECT 1 FROM app.schema_migrations WHERE version = 'V022__historical_case_prediction_visibility.sql'
            """
            ).fetchone()
            return row is not None
    except Exception:
        return False


class AuthenticationService(Protocol):
    """Minimal authentication port required by the HTTP interface."""

    async def login(self, username: str, password: str) -> AccessToken: ...

    async def identify(self, token: str) -> User: ...

    async def update_preferred_language(self, user: User, language: str) -> User: ...


class ParameterVersionService(Protocol):
    """Minimal parameter command port required by the HTTP interface."""

    def execute(
        self, command: CreateParameterVersionCommand, now: datetime
    ) -> ParameterVersion: ...


class OperationalReadService(Protocol):
    """Read projections required by P9.1 routes."""

    def config(self, now: datetime) -> dict[str, object]: ...
    def parameters(self, now: datetime) -> dict[str, object]: ...
    def users(self, role: str | None, now: datetime) -> list[dict[str, Any]]: ...
    def principal(self, user_id: str, now: datetime) -> dict[str, Any] | None: ...


def create_app(
    settings: Settings | None = None,
    auth: AuthenticationService | None = None,
    parameter_versions: ParameterVersionService | None = None,
    risk_orders: RiskOrderQueryPort | None = None,
    operational_reads: OperationalReadService | None = None,
    claim_case: ClaimCase | None = None,
    workflow_commands: WorkflowCommands | None = None,
    case_reads: CaseReads | None = None,
    evidence_files: EvidenceFiles | None = None,
) -> FastAPI:
    settings = settings or Settings(jwt_secret="change-me-in-production")
    auth = auth or build_auth_service(settings)
    parameter_versions = parameter_versions or build_parameter_version_service(settings)
    risk_orders = risk_orders or build_risk_order_query(settings)
    operational_reads = operational_reads or build_operational_reads(settings)
    claim_case = claim_case or build_claim_case(settings)
    workflow_commands = workflow_commands or build_workflow_commands(settings)
    reads: CaseReads = case_reads or build_case_reads(settings)
    evidence_files = evidence_files or build_evidence_store(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(title="Hidden Dissatisfaction API", version="0.5", lifespan=lifespan)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PATCH"],
            allow_headers=["Authorization", "Content-Type", "Accept-Language"],
        )

    @app.middleware("http")
    async def limit_request_size(request: Request, call_next: Any) -> Any:
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > settings.max_request_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request too large",
                        "details": None,
                    }
                },
            )
        return await call_next(request)

    security = HTTPBearer(auto_error=False)

    def error(code: str, message: str, details: dict[str, object] | None = None) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": code, "message": message, "details": details},
        )

    def user_response(user: User) -> UserResponse:
        principal_reader = getattr(operational_reads, "principal", None)
        workload = (
            principal_reader(str(user.id), datetime.now(UTC))
            if principal_reader
            else next(
                (
                    u
                    for u in operational_reads.users(user.role.value, datetime.now(UTC))
                    if str(u["user_id"]) == str(user.id)
                ),
                {},
            )
        ) or {}
        return UserResponse(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            preferred_language=user.preferred_language,
            created_at=user.created_at,
            active_count=workload.get("active_count"),
            capacity=workload.get("capacity"),
            slots_left=workload.get("slots_left"),
        )

    def queue_page_response(page: ApplicationQueuePage) -> PublicQueuePage:
        """Translate the application queue DTO into the public API DTO.

        Keeping this boundary explicit is important: the application page uses a
        tuple and contains a couple of internal fields which are not part of the
        HTTP contract.
        """
        return PublicQueuePage(
            items=[
                QueueOrder.model_validate(
                    {k: v for k, v in item.__dict__.items() if k in QueueOrder.model_fields}
                )
                for item in page.items
            ],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )

    def service() -> AuthenticationService:
        return auth

    async def current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
        svc: Annotated[AuthenticationService, Depends(service)],
    ) -> User:
        try:
            if credentials is None:
                raise InvalidToken
            return await svc.identify(credentials.credentials)
        except (InvalidToken, UserNotFound, ValueError, KeyError) as exc:
            raise HTTPException(
                401,
                detail={
                    "code": "UNAUTHENTICATED",
                    "message": "Invalid access token",
                    "details": None,
                },
            ) from exc

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    async def ready(ok: Annotated[bool, Depends(readiness_check)]) -> dict[str, str]:
        if not ok:
            raise HTTPException(503, detail={"code": "not_ready", "message": "Service not ready"})
        return {"status": "ok"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/auth/login", response_model=TokenResponse)
    async def login(
        body: LoginRequest, svc: Annotated[AuthenticationService, Depends(service)]
    ) -> TokenResponse:
        try:
            token = await svc.login(body.username, body.password)
        except InvalidCredentials as exc:
            raise HTTPException(
                401,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid credentials",
                    "details": None,
                },
            ) from exc
        user = await svc.identify(token.token)
        return TokenResponse(token=token.token, user=user_response(user))

    @app.post("/api/v1/auth/logout", status_code=204)
    async def logout(_: Annotated[User, Depends(current_user)]) -> None:
        return None

    @app.get("/api/v1/auth/me", response_model=UserResponse)
    async def me(user: Annotated[User, Depends(current_user)]) -> UserResponse:
        return user_response(user)

    @app.patch("/api/v1/auth/me", response_model=UserResponse)
    async def update_me(
        body: UpdateMeRequest, user: Annotated[User, Depends(current_user)]
    ) -> UserResponse:
        if body.preferred_language not in {"vi", "en"}:
            raise HTTPException(
                422,
                detail={"code": "VALIDATION_ERROR", "message": "Invalid language", "details": None},
            )
        return user_response(
            await service().update_preferred_language(user, body.preferred_language)
        )

    @app.post("/api/v1/parameters", response_model=ParameterVersionResponse, status_code=201)
    async def create_parameter_version(
        body: CreateParameterVersionRequest,
        user: Annotated[User, Depends(current_user)],
    ) -> ParameterVersionResponse:
        require_manager(user)
        now = datetime.now(UTC)
        try:
            version = parameter_versions.execute(
                CreateParameterVersionCommand(
                    key=body.key,
                    value=body.value,
                    effective_at=body.effective_at,
                    reason=body.reason,
                    actor_id=user.id,
                ),
                now,
            )
        except ParameterValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": exc.code, "message": str(exc), "details": None},
            ) from exc
        return ParameterVersionResponse(
            **version.__dict__,
            status="SCHEDULED" if version.effective_at > now else "ACTIVE",
        )

    @app.get("/api/v1/config")
    async def get_config(_: Annotated[User, Depends(current_user)]) -> dict[str, object]:
        try:
            return operational_reads.config(datetime.now(UTC))
        except LookupError as exc:
            raise HTTPException(503, detail={"code": "NOT_READY", "message": str(exc)}) from exc

    @app.get("/api/v1/parameters")
    async def list_parameters(user: Annotated[User, Depends(current_user)]) -> dict[str, object]:
        require_manager(user)
        return operational_reads.parameters(datetime.now(UTC))

    @app.get("/api/v1/users")
    async def list_users(
        _: Annotated[User, Depends(current_user)], role: str | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        if role is not None and role not in {"SPECIALIST", "MANAGER"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": "Invalid role", "details": None},
            )
        return {"items": operational_reads.users(role, datetime.now(UTC))}

    @app.get("/api/v1/orders", response_model=PublicQueuePage)
    async def list_orders(
        user: Annotated[User, Depends(current_user)],
        q: str | None = None,
        level: str | None = None,
        status_filter: Annotated[str, Query(alias="status")] = "OPEN",
        assignee: str | None = None,
        smin: float | None = None,
        smax: float | None = None,
        from_date: Annotated[datetime | None, Query(alias="from")] = None,
        to_date: Annotated[datetime | None, Query(alias="to")] = None,
        seller: str | None = None,
        category: str | None = None,
        outcome: str | None = None,
        sla: str | None = None,
        needs_decision: bool | None = None,
        sort: str = "priority",
        limit: int = 20,
        offset: int = 0,
    ) -> PublicQueuePage:
        if assignee == "me":
            assignee = str(user.id)
        try:
            page = risk_orders.list_orders(
                QueueFilters(
                    query=q,
                    level=level,
                    status=status_filter,
                    assignee=assignee,
                    score_min=smin,
                    score_max=smax,
                    queued_from=from_date,
                    queued_to=to_date,
                    seller=seller,
                    category=category,
                    outcome=outcome,
                    sla=sla,
                    needs_decision=needs_decision,
                    sort=sort,
                    limit=limit,
                    offset=offset,
                )
            )
        except QueueQueryValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": str(exc), "details": None},
            ) from exc
        return queue_page_response(page)

    @app.get("/api/v1/orders/summary", response_model=QueueSummary)
    async def order_summary(user: Annotated[User, Depends(current_user)]) -> QueueSummary:
        specialist = user.role is Role.SPECIALIST
        principal_reader = getattr(operational_reads, "principal", None)
        me_data = (
            principal_reader(str(user.id), datetime.now(UTC))
            if principal_reader
            else next(
                (
                    u
                    for u in operational_reads.users(user.role.value, datetime.now(UTC))
                    if str(u["user_id"]) == str(user.id)
                ),
                None,
            )
        )
        me = Principal.model_validate(me_data or user_response(user).model_dump())
        summary = summarize_queue(risk_orders, specialist=specialist, slots_left=me.slots_left)
        first = summary.first_pending
        return QueueSummary(
            **{k: v for k, v in summary.__dict__.items() if k != "first_pending"},
            first_pending=(
                QueueOrder.model_validate(
                    {k: v for k, v in first.__dict__.items() if k in QueueOrder.model_fields}
                )
                if first
                else None
            ),
            me=me,
        )

    @app.get("/api/v1/orders/filter-options")
    async def order_filter_options(
        _: Annotated[User, Depends(current_user)],
    ) -> dict[str, tuple[str, ...]]:
        return risk_orders.filter_options()

    @app.post("/api/v1/orders/{order_id}/claim", response_model=ClaimResponse)
    async def claim_order(
        order_id: str, user: Annotated[User, Depends(current_user)]
    ) -> ClaimResponse:
        if user.role is not Role.SPECIALIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Only Specialists can claim cases",
                    "details": None,
                },
            )
        try:
            result = claim_case.execute(order_id, user.id)
            refreshed = risk_orders.get_order(order_id)
        except ClaimNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ORDER_NOT_FOUND", "message": "Order not found", "details": None},
            ) from exc
        except ClaimConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ALREADY_CLAIMED",
                    "message": "Case was already claimed",
                    "details": None,
                },
            ) from exc
        except WorkflowPolicyError as exc:
            code = exc.code
            http_status = (
                status.HTTP_403_FORBIDDEN
                if code == "HIGH_RISK_REQUIRES_ASSIGN"
                else (
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                    if code == "CAPACITY_FULL"
                    else status.HTTP_409_CONFLICT
                )
            )
            raise HTTPException(
                status_code=http_status,
                detail={"code": code, "message": str(exc), "details": None},
            ) from exc
        if refreshed is None:
            raise RuntimeError("Claimed case is absent from the Queue projection")
        order = QueueOrder.model_validate(
            {k: v for k, v in refreshed.__dict__.items() if k in QueueOrder.model_fields}
        )
        principal = Principal.model_validate(user_response(user).model_dump()).model_copy(
            update={
                "active_count": result.active_count,
                "capacity": result.capacity,
                "slots_left": result.capacity - result.active_count,
            }
        )
        return ClaimResponse(order=order, me=principal)

    app.include_router(
        build_workflow_router(current_user, workflow_commands, reads, evidence_files)
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        language = _.headers.get("accept-language", "en").lower()
        message = "Dữ liệu không hợp lệ" if language.startswith("vi") else "Validation error"
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": message, "details": None}},
        )

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        detail = (
            exc.detail
            if isinstance(exc.detail, dict)
            else {"code": "HTTP_ERROR", "message": str(exc.detail), "details": None}
        )
        detail.setdefault("details", None)
        return JSONResponse(status_code=exc.status_code, content={"error": detail})

    return app
