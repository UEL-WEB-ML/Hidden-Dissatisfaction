from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hidden_dissatisfaction.domain.auth import Role


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    token: str
    user: "UserResponse"


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    username: str
    full_name: str
    role: Role
    preferred_language: str | None = None
    created_at: datetime | None = None
    active_count: int | None = None
    capacity: int | None = None
    slots_left: int | None = None


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preferred_language: str


class CreateParameterVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1, max_length=40)
    value: int | str
    effective_at: datetime
    reason: str = Field(min_length=1, max_length=1_000)


class ParameterVersionResponse(BaseModel):
    key: str
    value: str
    version: int
    effective_at: datetime
    actor_id: UUID
    reason: str
    created_at: datetime


class QueueOrderResponse(BaseModel):
    order_id: str
    score: float
    level: str
    status: str
    assignee_id: str | None
    assignee_name: str | None
    queued_at: datetime
    sla_due_at: datetime | None
    row_version: int
    matched_item_id: str | None = None


class QueuePageResponse(BaseModel):
    items: list[QueueOrderResponse]
    total: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
