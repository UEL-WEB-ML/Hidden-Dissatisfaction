from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
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
    security = HTTPBearer()

    def service() -> AuthService:
        if auth is None:
            raise RuntimeError("Auth service is not configured")
        return auth

    async def current_user(
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
        svc: Annotated[AuthService, Depends(service)],
    ) -> User:
        try:
            return await svc.identify(credentials.credentials)
        except (InvalidToken, UserNotFound, ValueError, KeyError) as exc:
            raise HTTPException(
                401, detail={"code": "invalid_token", "message": "Invalid access token"}
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

    @app.post("/auth/login", response_model=TokenResponse)
    async def login(
        body: LoginRequest, svc: Annotated[AuthService, Depends(service)]
    ) -> TokenResponse:
        try:
            token = await svc.login(str(body.email), body.password)
        except InvalidCredentials as exc:
            raise HTTPException(
                401, detail={"code": "invalid_credentials", "message": "Invalid credentials"}
            ) from exc
        return TokenResponse(access_token=token.token, expires_at=token.expires_at)

    @app.post("/auth/logout", status_code=204)
    async def logout(_: Annotated[User, Depends(current_user)]) -> None:
        return None

    @app.get("/me", response_model=UserResponse)
    async def me(user: Annotated[User, Depends(current_user)]) -> UserResponse:
        return UserResponse(id=user.id, email=user.email)

    @app.patch("/me", response_model=UserResponse)
    async def update_me(
        body: UpdateMeRequest, user: Annotated[User, Depends(current_user)]
    ) -> UserResponse:
        if body.preferred_language not in {"vi", "en"}:
            raise HTTPException(
                422, detail={"code": "validation_error", "message": "Invalid language"}
            )
        return UserResponse(
            id=user.id, email=user.email, preferred_language=body.preferred_language
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        language = _.headers.get("accept-language", "en").lower()
        message = "Dữ liệu không hợp lệ" if language.startswith("vi") else "Validation error"
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": message}},
        )

    return app
