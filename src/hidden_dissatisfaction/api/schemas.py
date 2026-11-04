from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hidden_dissatisfaction.domain.auth import Role


class Principal(BaseModel):
    """The authenticated principal and the workload counters shown to it."""

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


class TopItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_item_id: str
    category: str | None
    risk_score: float
    risk_level: str
    top_factors: list[str]
    synthetic_data_flag: bool
    model_version: str | None = None
    predicted_at: datetime | None = None
    data_source: str
    threshold_version: str | None = None
    aggregation_rule: str | None = None


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
    status: str


class QueueOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str
    risk_score: float
    risk_level: str
    status: str
    assignee_id: str | None
    assignee_name: str | None
    queued_at: datetime
    original_queued_at: datetime | None
    sla_due_at: datetime | None
    matched_item_id: str | None
    top_item: TopItem | None
    top_factors: list[str]
    items_count: int
    outcome: str | None
    skip_reason: str | None
    self_claim_allowed: bool
    contact_count: int = 0
    sla_state: str
    sla_hours_left: float | None
    aging_hours: float
    total_aging_hours: float
    is_escalated: bool
    is_stale: bool


class QueuePage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[QueueOrder]
    total: int
    limit: int
    offset: int


class StatusHistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    created_at: datetime
    actor_name: str
    event_type: str
    old_value: str | None = None
    new_value: str | None = None


class ItemDetail(TopItem):
    pass


class OrderDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order: "OrderDetailOrder"
    cycles: list["CycleDetail"]
    contacts: list["ContactDetail"]
    comments: list["CommentDetail"]
    decisions: list["DecisionDetail"]
    next_step: "NextStepDetail | None"
    model_notes: list["ModelNoteDetail"]
    audit_events: list["AuditEventDetail"] | None
    status_history: list[StatusHistoryEntry]
    seller_open_count: int


class OrderDetailOrder(QueueOrder):
    model_config = ConfigDict(extra="forbid")
    case_id: str | None = None
    aggregation_rule: str | None = None
    model_version: str | None = None
    predicted_at: datetime | None = None
    threshold_version: str | None = None
    seller_id: str | None = None
    category: str | None = None
    cycle_no: int | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    reopen_count: int | None = None
    needs_decision: bool | None = None
    has_synthetic_item: bool
    items: list[ItemDetail]


class CycleDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cycle_no: int
    started_at: datetime | None = None
    ended_at: datetime | None = None
    sla_due_at: datetime | None = None
    contact_count: int | None = None
    parameter_version: str


class ContactDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    contacted_at: datetime | None = None
    method: str | None = None
    result: str | None = None


class CommentDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str | None = None


class DecisionDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    decision: str | None = None


class NextStepDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    decision: str | None = None


class ModelNoteDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    note: str | None = None


class AuditEventDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    event_type: str | None = None


class QueueSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    high_pending: int
    high_pending_overdue: int
    overdue: int
    escalated: int
    stale: int
    needs_decision: int
    first_pending: QueueOrder | None
    me: Principal


class ClaimResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order: QueueOrder
    me: Principal


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
