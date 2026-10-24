from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    token: str
    user: "UserResponse"


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    username: str
    preferred_language: str | None = None


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preferred_language: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
