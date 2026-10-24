from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from hidden_dissatisfaction.application.auth import AuthService
from hidden_dissatisfaction.domain.auth import InvalidCredentials, InvalidToken, User, UserNotFound

from .config import Settings
from .schemas import LoginRequest, TokenResponse, UpdateMeRequest, UserResponse


async def readiness_check() -> bool:
    """Cheap readiness hook, intentionally replaceable in tests/deployment wiring."""
    return True


def create_app(settings: Settings | None = None, auth: AuthService | None = None) -> FastAPI:
    settings = settings or Settings(jwt_secret="change-me-in-production")

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(title="Hidden Dissatisfaction API", lifespan=lifespan)
    security = HTTPBearer(auto_error=False)

    def error(code: str, message: str, details: dict[str, object] | None = None) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": code, "message": message, "details": details},
        )

    def user_response(user: User, preferred_language: str | None = None) -> UserResponse:
        return UserResponse(
            id=user.id, username=user.username, preferred_language=preferred_language
        )

    def service() -> AuthService:
        if auth is None:
            raise RuntimeError("Auth service is not configured")
        return auth

    async def current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
        svc: Annotated[AuthService, Depends(service)],
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
        body: LoginRequest, svc: Annotated[AuthService, Depends(service)]
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
        return user_response(user, body.preferred_language)

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
